import os
import csv
from pathlib import Path
from dotenv import load_dotenv


def _load_env() -> None:
    # Load .env explicitly from project root (FANalyze_v2.0/.env), regardless of CWD
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=project_root / ".env", override=False)


def _get_snowflake_connection():
    import snowflake.connector
    from cryptography.hazmat.primitives import serialization

    sf_user = os.getenv("SNOWFLAKE_USER")
    sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
    sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    sf_database = os.getenv("SNOWFLAKE_DATABASE")
    sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    sf_role = os.getenv("SNOWFLAKE_ROLE")
    sf_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

    assert sf_user and sf_account and sf_private_key_path, (
        "Missing Snowflake env vars (require USER, ACCOUNT, and PRIVATE_KEY_PATH)."
    )

    with open(sf_private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )

    conn = snowflake.connector.connect(
        user=sf_user,
        account=sf_account,
        warehouse=sf_warehouse,
        database=sf_database,
        schema=sf_schema,
        role=sf_role,
        private_key=private_key,
    )
    return conn


def _ensure_schema_and_table(conn) -> None:
    # Create schema `testing` and table `testing.test_ingest` matching sample_data.csv
    # Columns in sample_data.csv: id,data_content,file_name
    ddl_statements = [
        "CREATE SCHEMA IF NOT EXISTS testing",
        """
        CREATE TABLE IF NOT EXISTS testing.test_ingest (
            id INTEGER,
            data_content STRING,
            file_name STRING,
            loaded_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
        )
        """,
    ]
    with conn.cursor() as cur:
        for ddl in ddl_statements:
            cur.execute(ddl)


def _truncate_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE IF EXISTS testing.test_ingest")


def _read_sample_csv(csv_path: str):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                (
                    int(r["id"]) if r["id"] is not None and r["id"] != "" else None,
                    r["data_content"],
                    r["file_name"],
                )
            )
    return rows


def _insert_rows(conn, rows) -> None:
    if not rows:
        return
    insert_sql = (
        "INSERT INTO testing.test_ingest (id, data_content, file_name, loaded_at) "
        "VALUES (%s, %s, %s, CURRENT_TIMESTAMP())"
    )
    with conn.cursor() as cur:
        cur.executemany(insert_sql, rows)


def _count_rows(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM testing.test_ingest")
        (count,) = cur.fetchone()
        return int(count)


def test_snowflake_upload_and_ingest() -> None:
    _load_env()

    conn = None
    try:
        conn = _get_snowflake_connection()

        _ensure_schema_and_table(conn)
        _truncate_table(conn)

        # Locate CSV next to this test file: tests/DB_tests/sample_data.csv
        csv_path = os.path.join(os.path.dirname(__file__), "sample_data.csv")
        assert os.path.exists(csv_path), f"CSV not found at {csv_path}"

        rows = _read_sample_csv(csv_path)
        assert len(rows) > 0, "No rows found in sample_data.csv"

        _insert_rows(conn, rows)

        ingested = _count_rows(conn)
        assert ingested == len(rows), (
            f"Row count mismatch: expected {len(rows)}, got {ingested}"
        )
    finally:
        if conn is not None:
            conn.close()
