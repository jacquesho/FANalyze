import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env() -> None:
    # Load .env explicitly from project root (FANalyze_v2.0/.env), regardless of CWD
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=project_root / ".env", override=False)


def test_postgres_connection() -> None:
    _load_env()

    import psycopg

    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    pg_db = os.getenv("POSTGRES_DB")
    pg_user = os.getenv("POSTGRES_USER")
    pg_password = os.getenv("POSTGRES_PASSWORD")

    assert pg_db and pg_user and pg_password, (
        "Missing Postgres env vars (POSTGRES_DB/USER/PASSWORD)."
    )

    conn = None
    try:
        conn = psycopg.connect(
            host=pg_host,
            port=pg_port,
            dbname=pg_db,
            user=pg_user,
            password=pg_password,
            connect_timeout=5,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            row = cur.fetchone()
            assert row == (1,), "Postgres connectivity check failed."
    finally:
        if conn is not None:
            conn.close()
