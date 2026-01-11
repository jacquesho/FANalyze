#!/usr/bin/env python3
"""
Execute flatten SQL to materialize testing.flat_shows
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console

# Ensure project root on path for `scripts.*` imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.database.sf_loader import get_snowflake_connection

load_dotenv()
console = Console()


def main() -> bool:
    sql_path = PROJECT_ROOT / "sql" / "flatten_setlistfm_testing.sql"
    sql_text = sql_path.read_text()

    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        console.print(f"🧱 Executing flatten SQL from {sql_path}", style="cyan")
        cur.execute(sql_text)
        console.print(
            "✅ Flatten tables created (testing.flat_shows, testing.flat_setlists)",
            style="green",
        )
        return True
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
