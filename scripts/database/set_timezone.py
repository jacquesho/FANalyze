#!/usr/bin/env python3
"""
Utility: Set and verify PostgreSQL session timezone for the ingest user.

- Reads connection details from .env (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
- Uses TIMEZONE env var if provided, else defaults to 'Asia/Bangkok'
"""

import os
import sys
import psycopg
from psycopg import sql
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table


def get_env_timezone() -> str:
    timezone = os.getenv("TIMEZONE")
    return timezone if timezone else "Asia/Bangkok"


def get_connection() -> psycopg.Connection | None:
    try:
        # Read strictly from environment (no hardcoded defaults)
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        dbname = os.getenv("POSTGRES_DB")
        # Require explicit ingest credentials only
        user = os.getenv("POSTGRES_USER_INGEST")
        password = os.getenv("POSTGRES_PASSWORD_INGEST")

        missing = [name for name, val in [
            ("POSTGRES_HOST", host),
            ("POSTGRES_PORT", port),
            ("POSTGRES_DB", dbname),
            ("POSTGRES_USER_INGEST", user),
            ("POSTGRES_PASSWORD_INGEST", password),
        ] if not val]

        if missing:
            console.print("❌ Missing required environment variables: " + ", ".join(missing), style="red")
            return None

        return psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
    except Exception as error:
        console.print(f"❌ Failed to connect to PostgreSQL: {error}", style="red")
        return None


def set_session_timezone(connection: psycopg.Connection, timezone: str) -> bool:
    try:
        with connection.cursor() as cursor:
            # Use a SQL literal instead of binding; SET TIME ZONE cannot use a parameter placeholder
            query = sql.SQL("SET TIME ZONE {};").format(sql.Literal(timezone))
            cursor.execute(query)
        connection.commit()
        return True
    except Exception as error:
        console.print(f"❌ Failed to set session timezone: {error}", style="red")
        return False


def show_session_info(connection: psycopg.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
        db_name, user_name, server_addr, server_port = cursor.fetchone()

        cursor.execute("SHOW TIMEZONE")
        tz = cursor.fetchone()[0]

        cursor.execute("SELECT NOW()")
        now_value = cursor.fetchone()[0]

    table = Table(title="PostgreSQL Session Info")
    table.add_column("Database", style="cyan")
    table.add_column("User", style="magenta")
    table.add_column("Server", style="green")
    table.add_column("Port", style="green")
    table.add_column("TimeZone", style="yellow")
    table.add_column("NOW()", style="yellow")
    table.add_row(str(db_name), str(user_name), str(server_addr), str(server_port), str(tz), str(now_value))
    console.print(table)


def main() -> int:
    console.print("🚀 Set PostgreSQL Session Timezone", style="bold blue")
    console.print("=" * 50)

    timezone = get_env_timezone()
    console.print(f"Requested timezone: {timezone}", style="cyan")

    connection = get_connection()
    if connection is None:
        return 1

    with connection:
        ok = set_session_timezone(connection, timezone)
        if not ok:
            return 1

        console.print("✅ Session timezone set successfully", style="green")
        show_session_info(connection)
        return 0


console = Console()

if __name__ == "__main__":
    load_dotenv()
    sys.exit(main())


