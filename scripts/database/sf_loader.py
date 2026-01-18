#!/usr/bin/env python3
"""
Snowflake Loader Utilities
- Ensures testing schema/tables exist (via SQL file)
- Loads JSON rows into VARIANT-based raw tables
"""

import os
from pathlib import Path
from typing import Iterable, Dict, Any
from dotenv import load_dotenv
from rich.console import Console

import snowflake.connector

load_dotenv()
console = Console()


def get_snowflake_connection():
    from cryptography.hazmat.primitives import serialization

    sf_user = os.getenv("SNOWFLAKE_USER")
    sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
    sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    sf_database = os.getenv("SNOWFLAKE_DATABASE")
    sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    sf_role = os.getenv("SNOWFLAKE_ROLE")
    sf_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

    with open(sf_private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    return snowflake.connector.connect(
        user=sf_user,
        account=sf_account,
        warehouse=sf_warehouse,
        database=sf_database,
        schema=sf_schema,
        role=sf_role,
        private_key=private_key,
    )


def _split_sql_statements(sql_text: str) -> list[str]:
    """Naively split SQL into statements by semicolons, skipping comment-only lines."""
    statements: list[str] = []
    buffer: list[str] = []
    for raw_line in sql_text.splitlines():
        line = raw_line.rstrip()
        # Skip single-line comments
        if line.strip().startswith("--"):
            continue
        buffer.append(line)
        if line.endswith(";"):
            stmt = "\n".join(buffer).strip()
            stmt = stmt[:-1].strip()  # remove trailing semicolon
            if stmt:
                statements.append(stmt)
            buffer = []
    # leftover
    tail = "\n".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def ensure_testing_tables(sql_file: Path) -> None:
    """Run a SQL file that contains multiple statements using sequential executes."""
    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        console.print(f"🔧 Running DDL from {sql_file}", style="cyan")
        sql_text = Path(sql_file).read_text()
        for stmt in _split_sql_statements(sql_text):
            cur.execute(stmt)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def _chunk(it, size):
    chunk = []
    for item in it:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def load_shows(rows: Iterable[Dict[str, Any]]) -> int:
    conn = get_snowflake_connection()
    cur = conn.cursor()
    inserted = 0
    try:
        # Use a TEMP table to stage JSON as VARCHAR, then parse in a single INSERT..SELECT.
        cur.execute(
            "CREATE TEMPORARY TABLE IF NOT EXISTS tmp_stage_shows (\n"
            "  artist_id STRING,\n"
            "  artist_name STRING,\n"
            "  show_id STRING,\n"
            "  show_date_str STRING,\n"
            "  payload_str STRING\n"
            ")"
        )
        stage_insert_sql = (
            "INSERT INTO tmp_stage_shows (artist_id, artist_name, show_id, show_date_str, payload_str) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        # Use per-row INSERT to avoid Snowflake multi-row rewrite issues with large JSON literals
        for r in rows:
            cur.execute(
                stage_insert_sql,
                (
                    r.get("artist_id"),
                    r.get("artist_name"),
                    r.get("show_id"),
                    r.get("show_date"),
                    r.get("payload_json"),
                ),
            )
            inserted += 1
            if inserted % 500 == 0:
                console.print(f"   • Staged {inserted} shows so far...", style="dim")

        # Move from temp stage into target with proper typing
        cur.execute(
            "INSERT INTO testing.raw_shows (artist_id, artist_name, show_id, show_date, payload)\n"
            "SELECT artist_id, artist_name, show_id, TO_DATE(show_date_str, 'DD-MM-YYYY'), PARSE_JSON(payload_str)\n"
            "FROM tmp_stage_shows"
        )
        # Cleanup temp table
        cur.execute("DROP TABLE IF EXISTS tmp_stage_shows")
        conn.commit()
        console.print(
            f"✅ Inserted {inserted} show rows into testing.raw_shows", style="green"
        )
        return inserted
    finally:
        cur.close()
        conn.close()


def load_setlists(rows: Iterable[Dict[str, Any]]) -> int:
    conn = get_snowflake_connection()
    cur = conn.cursor()
    inserted = 0
    try:
        cur.execute(
            "CREATE TEMPORARY TABLE IF NOT EXISTS tmp_stage_setlists (\n"
            "  artist_id STRING,\n"
            "  artist_name STRING,\n"
            "  setlist_id STRING,\n"
            "  show_id STRING,\n"
            "  payload_str STRING\n"
            ")"
        )
        stage_insert_sql = (
            "INSERT INTO tmp_stage_setlists (artist_id, artist_name, setlist_id, show_id, payload_str) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        for r in rows:
            cur.execute(
                stage_insert_sql,
                (
                    r.get("artist_id"),
                    r.get("artist_name"),
                    r.get("setlist_id"),
                    r.get("show_id"),
                    r.get("payload_json"),
                ),
            )
            inserted += 1
            if inserted % 500 == 0:
                console.print(
                    f"   • Staged {inserted} setlist rows so far...", style="dim"
                )

        cur.execute(
            "INSERT INTO testing.raw_setlists (artist_id, artist_name, setlist_id, show_id, payload)\n"
            "SELECT artist_id, artist_name, setlist_id, show_id, PARSE_JSON(payload_str)\n"
            "FROM tmp_stage_setlists"
        )
        cur.execute("DROP TABLE IF EXISTS tmp_stage_setlists")
        conn.commit()
        console.print(
            f"✅ Inserted {inserted} setlist rows into testing.raw_setlists",
            style="green",
        )
        return inserted
    finally:
        cur.close()
        conn.close()
