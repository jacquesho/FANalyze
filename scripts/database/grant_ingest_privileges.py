#!/usr/bin/env python3
"""
Grant required privileges for the ingest role to load data into staging tables.

Reads admin connection from .env:
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

Targets role:
  user_fanalyze_ingest (password not required here)

Grants:
  - CONNECT on database
  - USAGE on schema staging (creates schema if missing)
  - SELECT, INSERT, UPDATE, DELETE on ALL TABLES in staging
  - USAGE, SELECT, UPDATE on ALL SEQUENCES in staging
  - Default privileges for future tables/sequences in staging
"""

import os
import sys
import psycopg
from psycopg import sql
from dotenv import load_dotenv
from rich.console import Console


console = Console()


def require_env(names: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        value = os.getenv(name)
        if not value:
            missing.append(name)
        else:
            values[name] = value
    if missing:
        console.print(
            "❌ Missing required environment variables: " + ", ".join(missing),
            style="red",
        )
        sys.exit(1)
    return values


def admin_connect() -> psycopg.Connection:
    env = require_env(
        [
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
        ]
    )
    return psycopg.connect(
        host=env["POSTGRES_HOST"],
        port=env["POSTGRES_PORT"],
        dbname=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
    )


def grant_privileges(role_name: str) -> None:
    dbname = os.getenv("POSTGRES_DB")
    with admin_connect() as conn:
        with conn.cursor() as cur:
            console.print(f"🔐 Granting privileges to role '{role_name}'", style="cyan")

            # Ensure schema exists
            cur.execute("CREATE SCHEMA IF NOT EXISTS staging;")

            # CONNECT on database
            cur.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {};").format(
                    sql.Identifier(dbname), sql.Identifier(role_name)
                )
            )

            # Schema usage
            cur.execute(
                sql.SQL("GRANT USAGE ON SCHEMA staging TO {};").format(
                    sql.Identifier(role_name)
                )
            )

            # Existing objects in schema
            cur.execute(
                sql.SQL(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA staging TO {};"
                ).format(sql.Identifier(role_name))
            )
            cur.execute(
                sql.SQL(
                    "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA staging TO {};"
                ).format(sql.Identifier(role_name))
            )

            # Default privileges for future objects
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {};"
                ).format(sql.Identifier(role_name))
            )
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {};"
                ).format(sql.Identifier(role_name))
            )

        conn.commit()


def main() -> int:
    try:
        grant_privileges("user_fanalyze_ingest")
        console.print("✅ Privileges granted successfully", style="green")
        return 0
    except Exception as error:
        console.print(f"❌ Failed to grant privileges: {error}", style="red")
        return 1


if __name__ == "__main__":
    load_dotenv()
    sys.exit(main())
