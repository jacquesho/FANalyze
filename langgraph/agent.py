#!/usr/bin/env python3
"""
FANalyze LangGraph Agent with Tool Calling
Creates a persistent agent with PostgreSQL storage that can use:
- query_show_data: Query show data from Snowflake
- query_ticket_sales: Query ticket sales data from Snowflake
- search_documents: Search documents in Pinecone using RAG
"""

import os
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

# Import tools - handle both relative and absolute imports
try:
    from .tools import (
        query_show_data, 
        query_ticket_sales, 
        search_documents,
        _generate_show_data_query,
        _generate_ticket_sales_query,
        analyze_query_complexity,
    )
except ImportError:
    # Fallback for direct script execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from langgraph.tools import (
        query_show_data, 
        query_ticket_sales, 
        search_documents,
        _generate_show_data_query,
        _generate_ticket_sales_query,
        analyze_query_complexity,
    )

# Load environment variables
load_dotenv()


class MessagesState(TypedDict):
    """Agent state with messages and metadata"""

    messages: Annotated[list, add_messages]
    user_name: str
    conversation_count: int
    session_id: str
    thread_metadata: dict
    pending_query: dict  # For HITL: stores query info when awaiting approval


def create_postgres_connection():
    """Create PostgreSQL connection for checkpointing with timeout"""
    try:
        import psycopg
        
        # Get connection settings from environment variables (no defaults)
        host = os.getenv("LANGGRAPH_POSTGRES_HOST")
        port = os.getenv("LANGGRAPH_POSTGRES_PORT")
        database = os.getenv("LANGGRAPH_POSTGRES_DB")
        user = os.getenv("LANGGRAPH_POSTGRES_USER")
        password = os.getenv("LANGGRAPH_POSTGRES_PASSWORD")
        
        # Validate all required variables are set
        if not all([host, port, database, user, password]):
            return None

        db_uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        # Try connection with 3 second timeout
        try:
            # PostgresSaver doesn't need row_factory - use default connection
            connection = psycopg.connect(
                db_uri, 
                autocommit=True,
                connect_timeout=3  # 3 second timeout
            )
            # Test the connection
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
            return connection
        except (psycopg.OperationalError, psycopg.Error, TimeoutError) as e:
            # Connection failed - log the error for debugging
            print(f"⚠️  PostgreSQL connection failed: {e}")
            print(f"   Attempted: {user}@{host}:{port}/{database}")
            return None
    except ImportError:
        # psycopg not available
        print("⚠️  psycopg library not available")
        return None
    except Exception as e:
        # Any other error
        print(f"⚠️  Unexpected error connecting to PostgreSQL: {e}")
        return None


def create_fanalyze_agent():
    """Create FANalyze agent with tool-calling capabilities and PostgreSQL persistence"""

    # Initialize LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.1,  # Lower temperature for more consistent tool usage
    )

    # Create tool registry - all three tools
    tools = [query_show_data, query_ticket_sales, search_documents]
    tools_by_name = {tool.name: tool for tool in tools}

    # Augment the LLM with tools
    llm_with_tools = llm.bind_tools(tools)

    # Define the agent nodes
    def llm_call(state: MessagesState):
        """LLM decides whether to call a tool or not"""
        messages = state["messages"]
        user_name = state.get("user_name", "User")
        conversation_count = state.get("conversation_count", 0)

        # Create system message with tool descriptions
        system_message = SystemMessage(
            content=f"""You are a helpful AI assistant for FANalyze, a concert and ticket sales analytics platform.

You have access to three tools:
1. **query_show_data**: Query show data (past and future concerts) from Snowflake
   - Use when asked about concerts, shows, venues, artists, or concert schedules
   - Can filter by artist_name, show_type (past/future/all), and limit results

2. **query_ticket_sales**: Query real-time ticket sales data from Snowflake
   - Use when asked about ticket sales, revenue, or recent purchases
   - Can filter by artist_name, venue_name, hours (time window), and limit results

3. **search_documents**: Search FANalyze documents using RAG (Retrieval-Augmented Generation)
   - ALWAYS use this tool when asked about: musician biographies, artist histories, ticket sales strategies, pricing models, or any internal documentation
   - Searches through processed PDFs and documents stored in Pinecone
   - Returns relevant document chunks with semantic similarity

CRITICAL RULES:
- **ALWAYS use search_documents** when users ask about musicians, artists, biographies, histories, ticket strategies, or documentation
- **NEVER answer questions about musicians/artists/biographies** without first calling search_documents
- If the user explicitly asks to "only use Pinecone" or "only tell me what you find in Pinecone", you MUST:
  * Call search_documents tool
  * ONLY use information from the tool results
  * If no results found, say "I couldn't find that information in the Pinecone documents"
  * DO NOT supplement with your general knowledge
- When search_documents returns results, synthesize them into a clear answer
- When search_documents returns NO results (total_results: 0), tell the user you couldn't find that information in the documents
- For Snowflake data queries, always use the appropriate query tool
- Only answer general questions directly (like "what is Python?") without tools

User: {user_name}
Conversation: #{conversation_count + 1}"""
        )

        # Get response from LLM with tools
        response = llm_with_tools.invoke([system_message] + messages)
        return {"messages": [response]}

    def review_query(state: MessagesState) -> dict:
        """
        Review Snowflake queries before execution. 
        Interrupts if query is expensive, otherwise proceeds to execution.
        """
        print("🔍 review_query node called")
        last_message = state["messages"][-1]
        
        # Check for tool calls
        if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
            print("   No tool calls found, routing to tools")
            return {"_route": "tools"}
        
        print(f"   Found {len(last_message.tool_calls)} tool call(s)")
        
        # Check if any Snowflake tools are being called
        snowflake_tools = ["query_show_data", "query_ticket_sales"]
        query_info = None
        all_tool_calls = last_message.tool_calls  # Store all tool calls for proper response
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            if tool_name in snowflake_tools:
                # Generate the query
                args = tool_call["args"]
                if tool_name == "query_show_data":
                    query = _generate_show_data_query(
                        artist_name=args.get("artist_name"),
                        show_type=args.get("show_type", "all"),
                        limit=args.get("limit", 50)
                    )
                elif tool_name == "query_ticket_sales":
                    query = _generate_ticket_sales_query(
                        artist_name=args.get("artist_name"),
                        venue_name=args.get("venue_name"),
                        hours=args.get("hours"),  # None by default - queries all data
                        limit=args.get("limit", 50)
                    )
                
                # Analyze query complexity
                analysis = analyze_query_complexity(query)
                
                # Debug: print analysis (remove in production)
                print(f"🔍 Query Analysis for {tool_name}:")
                print(f"   Expensive: {analysis['is_expensive']}")
                print(f"   Reasons: {analysis['reasons']}")
                print(f"   Limit: {analysis['limit_value']}")
                
                if analysis["is_expensive"]:
                    # Store query info for approval (use first expensive query found)
                    if query_info is None:
                        query_info = {
                            "tool_name": tool_name,
                            "query": query,
                            "analysis": analysis,
                            "tool_call": tool_call,
                        }
        
        # If expensive query found, interrupt for approval
        if query_info:
            # Store query info for better formatting in Streamlit
            # The interrupt message will be simple, Streamlit will format the details
            formatted_query = query_info["query"].strip()
            reasons = query_info["analysis"]["reasons"]
            estimated_cost = query_info["analysis"]["estimated_cost"].upper()
            
            # Simple interrupt message - Streamlit will format the details nicely
            interrupt_msg = f"Expensive query detected: {query_info['tool_name']}"
            
            # Interrupt - execution pauses here, Streamlit will resume with Command(resume="yes"/"no")
            user_response = interrupt(interrupt_msg)
            
            # After resume, interrupt() returns the resume value
            if user_response and user_response.lower() == "yes":
                # User approved - proceed to tools (all tool_calls are already in state)
                return {"_route": "tools"}
            else:
                # User rejected - must respond to ALL tool_calls with ToolMessages
                # This satisfies LangChain's requirement that all tool_calls must have ToolMessage responses
                cancellation_messages = [
                    ToolMessage(
                        content="Query execution cancelled by user.",
                        tool_call_id=tc["id"]
                    )
                    for tc in all_tool_calls
                ]
                return {
                    "messages": [
                        *state["messages"],
                        *cancellation_messages
                    ],
                    "_route": "end"  # Signal to route to end
                }
        
        # No expensive queries, proceed normally (signal to route to tools)
        return {"_route": "tools"}

    def tool_node(state: dict):
        """Performs the tool calls - handles multiple tool calls"""
        result = []
        last_message = state["messages"][-1]
        
        # Check if we have a pending approved query
        pending_query = state.get("pending_query", {})
        if pending_query and pending_query.get("tool_call"):
            # Use the approved query's tool call (single tool call from approval)
            tool_calls_to_process = [pending_query["tool_call"]]
        elif hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Process ALL tool calls
            tool_calls_to_process = last_message.tool_calls
        else:
            tool_calls_to_process = []

        # Process each tool call
        for tool_call in tool_calls_to_process:
            tool_name = tool_call["name"]
            tool = tools_by_name.get(tool_name)

            if tool:
                try:
                    # Invoke the tool with the provided arguments
                    observation = tool.invoke(tool_call["args"])
                    # Convert result to string if it's a dict
                    if isinstance(observation, dict):
                        # Format search_documents results nicely
                        if tool_name == "search_documents":
                            content = _format_search_results(observation)
                        else:
                            content = str(observation)
                    else:
                        content = str(observation)

                    result.append(
                        ToolMessage(content=content, tool_call_id=tool_call["id"])
                    )
                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    result.append(
                        ToolMessage(content=error_msg, tool_call_id=tool_call["id"])
                    )
            else:
                error_msg = f"Unknown tool: {tool_name}"
                result.append(
                    ToolMessage(content=error_msg, tool_call_id=tool_call["id"])
                )

        return {"messages": result}

    def _format_search_results(results: dict) -> str:
        """Format search_documents results for better readability"""
        if results.get("error"):
            return f"ERROR: {results['error']}\n\nNo documents found in Pinecone."

        total_results = results.get("total_results", 0)
        if total_results == 0:
            return "NO_RESULTS: No documents found in Pinecone matching this query.\n\nPlease inform the user that you couldn't find this information in the Pinecone documents."

        formatted = f"Found {total_results} relevant document(s) in Pinecone:\n\n"
        for i, result in enumerate(results.get("results", [])[:5], 1):  # Show top 5
            score = result.get("relevance_score", 0)
            source = result.get("source", "Unknown")
            content = result.get("content", "")
            formatted += f"[{i}] (Relevance: {score:.3f}) From: {source}\n{content[:800]}\n\n"

        return formatted

    # Conditional edge function to route based on tool calls
    def should_continue(state: MessagesState) -> Literal["tools", "end"]:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM makes a tool call, then perform an action
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, we stop (reply to the user)
        return "end"

    # Build workflow
    agent_builder = StateGraph(MessagesState)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("review_query", review_query)
    agent_builder.add_node("tools", tool_node)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        {
            "tools": "review_query",  # Route through review_query first
            "end": END,
        },
    )
    # Route after review_query based on _route signal
    def route_after_review(state: MessagesState) -> Literal["tools", "end"]:
        """Route after review_query based on _route signal in state"""
        # _route is added by review_query return value (merged into state)
        # Access it as a dict key (LangGraph merges return dicts into state)
        route = state.get("_route", "tools")  # type: ignore
        return route
    
    agent_builder.add_conditional_edges(
        "review_query",
        route_after_review,
        {
            "tools": "tools",
            "end": END,
        },
    )
    agent_builder.add_edge("tools", "llm_call")

    # Try PostgreSQL first, fall back to in-memory if not available
    # Use the existing create_postgres_connection() function
    connection = create_postgres_connection()
    
    if connection is None:
        print("⚠️  PostgreSQL not available - using in-memory storage")
        print("💡 Note: Conversations won't persist across sessions")
        from langgraph.checkpoint.memory import InMemorySaver
        memory = InMemorySaver()
    else:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            
            # Create PostgresSaver with the connection
            # The connection is already tested and working from create_postgres_connection()
            memory = PostgresSaver(connection)
            memory.setup()  # Create necessary tables
            print("✅ Connected to PostgreSQL for persistent storage")
        except Exception as e:
            print(f"⚠️  Failed to setup PostgreSQL checkpointing: {e}")
            import traceback
            traceback.print_exc()
            print("💡 Falling back to in-memory storage")
            from langgraph.checkpoint.memory import InMemorySaver
            memory = InMemorySaver()

    # Compile the agent with persistent memory
    agent = agent_builder.compile(checkpointer=memory)

    return agent


def create_persistent_agent():
    """Alias for create_fanalyze_agent for compatibility with streamlit_app"""
    return create_fanalyze_agent()


if __name__ == "__main__":
    # Test the agent
    print("🤖 Testing FANalyze Agent")
    print("=" * 60)

    agent = create_fanalyze_agent()

    # Test query
    test_config = {"configurable": {"thread_id": "test_thread"}}
    initial_state = {
        "messages": [HumanMessage(content="What shows are coming up?")],
        "user_name": "Test User",
        "conversation_count": 0,
        "session_id": "test_session",
        "thread_metadata": {},
    }

    print("\n📝 Test Query: 'What shows are coming up?'")
    result = agent.invoke(initial_state, test_config)
    print(f"\n✅ Response: {result['messages'][-1].content[:200]}...")


