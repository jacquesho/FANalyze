#!/usr/bin/env python3
"""
FANalyze Agent Tools
Tools for querying Snowflake data warehouse (batch and real-time data)
and searching documents using hybrid search with reranking.

Available tools:
- query_show_data: Query show data (past and future concerts)
- query_ticket_sales: Query real-time ticket sales data
- search_documents: Search documents using hybrid search (dense + sparse) with reranking
"""

import os
import sys
from pathlib import Path
from typing import Any, Optional
from langchain_core.tools import tool
from dotenv import load_dotenv

# Add project root to path for config imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

from config.api_config import get_snowflake_connection
from rag.retrieval import DocumentRetriever


def _generate_show_data_query(
    artist_name: Optional[str] = None, show_type: str = "all", limit: int = 50
) -> str:
    """Generate SQL query for show data without executing it"""
    where_clauses = []

    if artist_name:
        where_clauses.append(f"LOWER(da.artist_name) LIKE LOWER('%{artist_name}%')")

    if show_type.lower() == "past":
        where_clauses.append("fs.show_status = 'Historical'")
    elif show_type.lower() == "future":
        where_clauses.append("fs.show_status = 'Upcoming'")

    where_clause = ""
    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses)

    query = f"""
    SELECT 
        COALESCE(da.artist_name, 'Unknown') as artist_name,
        fs.show_date,
        fs.show_status,
        fs.city_name,
        fs.state_code,
        fs.country_name,
        COALESCE(dv.venue_name, 'Unknown') as venue_name,
        fs.venue_capacity,
        fs.tickets_sold,
        fs.revenue,
        fs.days_from_show
    FROM fact_shows fs
    LEFT JOIN dim_artists da ON fs.artist_id = da.artist_id
    LEFT JOIN dim_venues dv ON fs.venue_id = dv.venue_id
    {where_clause}
    ORDER BY 
        CASE WHEN fs.show_status = 'Upcoming' THEN 0 ELSE 1 END,
        fs.show_date DESC
    LIMIT {limit}
    """
    return query.strip()


def _generate_ticket_sales_query(
    artist_name: Optional[str] = None,
    venue_name: Optional[str] = None,
    hours: Optional[int] = None,
    limit: int = 50,
) -> str:
    """Generate SQL query for ticket sales without executing it"""
    where_clauses = []

    if artist_name:
        where_clauses.append(f"LOWER(artist_name) LIKE LOWER('%{artist_name}%')")

    if venue_name:
        where_clauses.append(f"LOWER(venue_name) LIKE LOWER('%{venue_name}%')")

    # Only add time filter if hours is specified
    if hours is not None:
        where_clauses.append(
            f"timestamp >= DATEADD(hour, -{hours}, CURRENT_TIMESTAMP())"
        )

    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
    SELECT 
        artist_name,
        venue_name,
        show_date,
        timestamp as sale_timestamp,
        tickets_sold,
        cumulative_tickets_sold,
        revenue,
        cumulative_revenue,
        sales_rate,
        demand_category,
        venue_utilization_pct,
        days_until_show
    FROM fact_ticket_sales
    {where_clause}
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    return query.strip()


def analyze_query_complexity(query: str) -> dict[str, Any]:
    """
    Analyze a SQL query to determine if it's expensive/complex.

    Returns:
        dict with keys:
        - is_expensive: bool
        - reasons: list of strings explaining why it's expensive
        - estimated_cost: str (low/medium/high)
        - limit_value: int or None
    """
    query_upper = query.upper()
    reasons = []
    is_expensive = False

    # Check for LIMIT
    limit_match = None
    import re

    limit_pattern = r"LIMIT\s+(\d+)"
    limit_match = re.search(limit_pattern, query_upper)
    limit_value = int(limit_match.group(1)) if limit_match else None

    # Check 1: No LIMIT clause
    if not limit_match:
        is_expensive = True
        reasons.append("No LIMIT clause - could return unlimited rows")

    # Check 2: Large LIMIT (>= 100)
    elif limit_value and limit_value >= 100:
        is_expensive = True
        reasons.append(f"Large LIMIT ({limit_value}) - may return many rows")

    # Check 3: Multiple JOINs (complexity indicator)
    join_count = query_upper.count("JOIN")
    if join_count > 2:
        is_expensive = True
        reasons.append(f"Multiple JOINs ({join_count}) - complex query")

    # Check 4: Subqueries
    if "SELECT" in query_upper and query_upper.count("SELECT") > 1:
        is_expensive = True
        reasons.append("Contains subqueries - complex execution")

    # Check 5: No WHERE clause (full table scan) - ALWAYS flag
    if "WHERE" not in query_upper:
        is_expensive = True
        if limit_value:
            reasons.append(
                f"No WHERE clause - scans entire table before LIMIT {limit_value}"
            )
        else:
            reasons.append("No WHERE clause and no LIMIT - dangerous full table scan")

    # Check 5b: Broad queries with minimal filters (e.g., "all future concerts" with no artist)
    # These still scan large portions of the table
    if "WHERE" in query_upper:
        # Check if WHERE only has show_status filter (broad query)
        # This is a heuristic - if WHERE only contains status filter, it's still scanning a lot
        where_content = (
            query_upper.split("WHERE")[1].split("ORDER")[0]
            if "ORDER" in query_upper
            else query_upper.split("WHERE")[1]
        )
        # Count meaningful filters (not just status)
        has_artist_filter = (
            "ARTIST_NAME" in where_content or "ARTIST_ID" in where_content
        )
        has_venue_filter = "VENUE" in where_content or "CITY" in where_content
        has_status_filter = "SHOW_STATUS" in where_content

        # If only status filter (broad query) and limit >= 50, flag it
        if has_status_filter and not has_artist_filter and not has_venue_filter:
            if limit_value and limit_value >= 50:
                is_expensive = True
                reasons.append(
                    f"Broad query - only status filter, scans large portion of table (LIMIT {limit_value})"
                )

    # Check 6: Broad queries with only time-based filters (ticket_sales always has timestamp)
    # If query has WHERE but only timestamp filter, it's still scanning all recent data
    # This is less critical but worth flagging for large limits
    if "WHERE" in query_upper and limit_value and limit_value >= 100:
        # Check if WHERE only contains timestamp/date filters (common in ticket_sales)
        # This is a heuristic - if WHERE exists but limit is large, might be expensive
        if "TIMESTAMP" in query_upper or "DATEADD" in query_upper:
            # Has time filter but large limit - might still be expensive
            if limit_value >= 100:
                is_expensive = True
                reasons.append(
                    f"Large LIMIT ({limit_value}) with time-based filter - may scan many rows"
                )

    # Determine cost level
    if is_expensive:
        if limit_value and limit_value > 200 or not limit_match:
            estimated_cost = "high"
        elif limit_value and limit_value > 100 or join_count > 2:
            estimated_cost = "medium"
        else:
            estimated_cost = "low"
    else:
        estimated_cost = "low"

    return {
        "is_expensive": is_expensive,
        "reasons": reasons,
        "estimated_cost": estimated_cost,
        "limit_value": limit_value,
        "join_count": join_count,
    }


def _execute_snowflake_query(query: str, limit: int = 100) -> str:
    """
    Internal helper to execute Snowflake queries safely.

    Args:
        query: SQL SELECT query
        limit: Maximum rows to return

    Returns:
        Formatted query results as string
    """
    # Safety check: Only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for security."

    # Get database from env (schema is FAN_MARTS for marts tables)
    database = os.getenv("SNOWFLAKE_DATABASE", "FANALYZE")
    schema = "FAN_MARTS"  # marts tables are in FAN_MARTS schema

    conn = None
    cursor = None
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Use the correct database and schema
        cursor.execute(f"USE DATABASE {database}")
        cursor.execute(f"USE SCHEMA {schema}")

        # Debug: Check what database/schema we're actually using
        cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
        db_info = cursor.fetchone()
        actual_db, actual_schema = db_info

        # Use fully qualified table names to be safe
        # Replace table names in query with fully qualified names (case-insensitive)
        import re

        query = re.sub(
            r"\bfact_shows\b",
            f"{actual_db}.{actual_schema}.fact_shows",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"\bfact_ticket_sales\b",
            f"{actual_db}.{actual_schema}.fact_ticket_sales",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"\bdim_artists\b",
            f"{actual_db}.{actual_schema}.dim_artists",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"\bdim_venues\b",
            f"{actual_db}.{actual_schema}.dim_venues",
            query,
            flags=re.IGNORECASE,
        )

        # Add limit if not present (for safety)
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        if not results:
            return f"Query executed successfully but returned no results.\n\nQuery: {query[:200]}..."

        # Format results
        formatted = f"[OK] Found {len(results)} row(s):\n\n"

        # Header
        header = " | ".join(str(col).ljust(20) for col in columns)
        formatted += header + "\n"
        formatted += "-" * min(len(header), 120) + "\n"

        # Rows (limit display to avoid huge outputs)
        display_limit = min(len(results), limit)
        for row in results[:display_limit]:
            row_str = " | ".join(
                str(val)[:20].ljust(20) if val is not None else "NULL".ljust(20)
                for val in row
            )
            formatted += row_str + "\n"

        if len(results) > display_limit:
            formatted += f"\n... (showing {display_limit} of {len(results)} rows)"

        return formatted

    except Exception as e:
        error_msg = f"[ERROR] Query error: {str(e)}\n\n"
        error_msg += "Hint: Check table names and column names match the schema.\n"
        error_msg += "Available schemas: FAN_MARTS (for fact_shows, fact_ticket_sales, dim_artists, etc.)\n"
        if conn and cursor:
            try:
                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
                db_info = cursor.fetchone()
                error_msg += (
                    f"Current database: {db_info[0]}, Current schema: {db_info[1]}\n"
                )
                # Try to list tables in current schema
                cursor.execute(f"SHOW TABLES IN SCHEMA {db_info[0]}.{db_info[1]}")
                tables = cursor.fetchall()
                if tables:
                    table_names = [
                        t[1] for t in tables
                    ]  # Table name is usually in second column
                    error_msg += f"Available tables: {', '.join(table_names[:10])}\n"
            except Exception:
                pass
        return error_msg
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@tool
def query_show_data(
    artist_name: Optional[str] = None, show_type: str = "all", limit: int = 50
) -> str:
    """
    Query show data including both past (historical) and future (upcoming) shows.

    Use this tool for questions about:
    - Upcoming concerts
    - Past concerts
    - All shows (past + future)
    - Show status and dates

    Args:
        artist_name: Filter by artist name (e.g., 'Metallica', 'Iron Maiden')
        show_type: Type of shows to return - 'past', 'future', or 'all' (default: 'all')
        limit: Maximum number of results to return (default: 50)

    Returns:
        Formatted results with show details including status, date, venue, city
    """
    # Generate query using helper
    query = _generate_show_data_query(artist_name, show_type, limit)
    return _execute_snowflake_query(query, limit)


@tool
def query_ticket_sales(
    artist_name: Optional[str] = None,
    venue_name: Optional[str] = None,
    hours: Optional[int] = None,
    limit: int = 50,
) -> str:
    """
    Query ticket sales data from the streaming pipeline.

    Use this tool for questions about:
    - Ticket sales (all time or recent)
    - Sales activity
    - Demand signals
    - Sales velocity and trends

    This queries data from the Kafka → PostgreSQL → Snowflake pipeline.
    By default, queries ALL ticket sales data. Use the hours parameter to filter by time window.

    Args:
        artist_name: Filter by artist name (e.g., 'Metallica')
        venue_name: Filter by venue name
        hours: Optional - Number of hours to look back for recent sales. If not provided, queries all data.
        limit: Maximum number of results to return (default: 50)

    Returns:
        Formatted results with ticket sales data including timestamp, tickets sold, revenue, sales rate
    """
    # Generate query using helper
    query = _generate_ticket_sales_query(artist_name, venue_name, hours, limit)
    return _execute_snowflake_query(query, limit)


@tool
def search_documents(
    query: str,
    top_k: int = 5,
    use_hybrid: bool = True,
    use_reranking: bool = True,
) -> dict[str, Any]:
    """
    Search for information in FANalyze documents stored in Pinecone using hybrid search (semantic + keyword) with reranking.

    **CRITICAL: ALWAYS use this tool when users ask about:**
    - Musician biographies, artist histories, or how bands/artists got started
    - Ticket sales strategies, pricing models, or sales protocols
    - Any information about artists, musicians, or bands (Metallica, Taylor Swift, etc.)
    - Internal documentation or reports

    This tool searches through processed documents stored in Pinecone including:
    - Musician biographies and histories (e.g., Metallica's history, Taylor Swift's early career)
    - Ticket sales strategies and pricing models
    - Internal documentation and reports

    Uses advanced retrieval techniques:
    - Hybrid search: Combines semantic understanding (dense vectors) with exact keyword matching (sparse vectors)
    - Reranking: Reorders results by relevance using Pinecone's reranking model

    **IMPORTANT:** If the user asks about an artist/musician/band, you MUST use this tool. Do NOT rely on general knowledge.

    Args:
        query: Search query describing what information to find
        top_k: Number of top results to return (default: 5)
        use_hybrid: Whether to use hybrid search combining dense and sparse vectors (default: True)
        use_reranking: Whether to rerank results for better relevance (default: True)

    Returns:
        Dictionary containing:
        - query: The search query
        - total_results: Number of results found
        - results: List of relevant document chunks with text, source, and scores
        - search_method: "hybrid" or "dense"
        - reranked: Whether results were reranked
    """
    try:
        retriever = DocumentRetriever()
        results = retriever.search(
            query=query,
            top_k=10,  # Retrieve more initially for reranking
            use_hybrid=use_hybrid,
            use_reranking=use_reranking,
            rerank_top_k=top_k,
        )

        # Format results for LangChain tool response
        if results.get("error"):
            return {
                "error": results["error"],
                "query": query,
                "results": [],
                "suggestion": "Check Pinecone configuration and try again.",
            }

        # Format results with truncated text for display
        formatted_results = []
        for result in results.get("results", []):
            text = result.get("text", "")
            # Truncate long text for tool response (full text available in metadata)
            display_text = text[:1000] + "..." if len(text) > 1000 else text

            formatted_results.append(
                {
                    "relevance_score": result.get("rerank_score")
                    or result.get("similarity_score", 0),
                    "content": display_text,
                    "source": result.get("source", "Unknown"),
                    "chunk_id": result.get("chunk_id", ""),
                    "metadata": result.get("metadata", {}),
                }
            )

        return {
            "query": query,
            "total_results": len(formatted_results),
            "results": formatted_results,
            "search_method": results.get("search_method", "hybrid"),
            "reranked": results.get("reranked", False),
            "index_name": results.get("index_name", "unknown"),
        }

    except Exception as e:
        return {
            "error": f"Failed to search documents: {str(e)}",
            "query": query,
            "results": [],
            "suggestion": "Check Pinecone configuration and try again.",
        }


# Export all tools and helpers
__all__ = [
    "query_show_data",
    "query_ticket_sales",
    "search_documents",
    "_generate_show_data_query",
    "_generate_ticket_sales_query",
    "analyze_query_complexity",
]
