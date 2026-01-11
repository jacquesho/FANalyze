#!/usr/bin/env python3
"""
Recreate the PostgreSQL ingest user (`user_fanalyze_ingest`).

- Connects with admin credentials from .env (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
- Terminates any active sessions for the ingest user
- Drops owned objects (safe reset) and the role if it exists
- Creates the role with LOGIN and password from POSTGRES_PASSWORD_INGEST
- Sets the role-level timezone to POSTGRES_INGEST_TIMEZONE (or TIMEZONE if provided)
- Grants CONNECT on the target database and basic schema privileges on `staging`

This script makes no assumptions about existing schemas/tables, but will create the
`staging` schema if missing to ensure grants succeed.
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
        if value is None or value == "":
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


def recreate_user() -> int:
    env = require_env(["POSTGRES_PASSWORD_INGEST"])  # required
    # Timezone comes from POSTGRES_INGEST_TIMEZONE, else fall back to TIMEZONE if set, else default Asia/Bangkok.
    timezone = (
        os.getenv("POSTGRES_INGEST_TIMEZONE") or os.getenv("TIMEZONE") or "Asia/Bangkok"
    )

    target_user = "user_fanalyze_ingest"

    with admin_connect() as conn:
        with conn.cursor() as cur:
            console.print(
                f"🔌 Connected as admin. Recreating role '{target_user}'", style="cyan"
            )

            # Terminate active sessions of the target user
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE usename = %s
                  AND pid <> pg_backend_pid();
                """,
                (target_user,),
            )

            # Drop owned objects then drop the role if it exists
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (target_user,))
            exists = cur.fetchone() is not None
            if exists:
                cur.execute(
                    sql.SQL("DROP OWNED BY {} CASCADE").format(
                        sql.Identifier(target_user)
                    )
                )
                cur.execute(
                    sql.SQL("DROP ROLE IF EXISTS {};").format(
                        sql.Identifier(target_user)
                    )
                )
            else:
                cur.execute(
                    sql.SQL("DROP ROLE IF EXISTS {};").format(
                        sql.Identifier(target_user)
                    )
                )

            # Create the role with password and login (use literal for password)
            cur.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {};").format(
                    sql.Identifier(target_user),
                    sql.Literal(env["POSTGRES_PASSWORD_INGEST"]),
                )
            )

            # Set role-level timezone (use literal for value)
            cur.execute(
                sql.SQL("ALTER ROLE {} SET TIMEZONE = {};").format(
                    sql.Identifier(target_user), sql.Literal(timezone)
                )
            )

            # Ensure staging schema exists
            cur.execute("CREATE SCHEMA IF NOT EXISTS staging;")

            # Grant basic privileges
            # CONNECT on target database
            dbname = os.getenv("POSTGRES_DB")
            cur.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {};").format(
                    sql.Identifier(dbname), sql.Identifier(target_user)
                )
            )
            # Schema usage and default privileges in staging
            cur.execute(
                sql.SQL("GRANT USAGE ON SCHEMA staging TO {};").format(
                    sql.Identifier(target_user)
                )
            )
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {};"
                ).format(sql.Identifier(target_user))
            )

        conn.commit()

    console.print("✅ Role recreated and configured successfully", style="green")
    console.print(f"   • Timezone set to: {timezone}", style="cyan")
    return 0


def main() -> int:
    try:
        return recreate_user()
    except Exception as error:
        console.print(f"❌ Failed to recreate ingest user: {error}", style="red")
        return 1


if __name__ == "__main__":
    load_dotenv()
    sys.exit(main())
