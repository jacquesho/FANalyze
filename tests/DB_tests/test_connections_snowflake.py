import os

from dotenv import load_dotenv


def _load_env() -> None:
    # Load .env from project root (FANalyze_v2.0/.env)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(root_dir, ".env")
    load_dotenv(dotenv_path=dotenv_path, override=False)


def test_snowflake_connection() -> None:
    _load_env()

    import snowflake.connector

    sf_user = os.getenv("SNOWFLAKE_USER")
    sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
    sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    sf_database = os.getenv("SNOWFLAKE_DATABASE")
    sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    sf_role = os.getenv("SNOWFLAKE_ROLE")
    sf_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

    assert (
        sf_user and sf_account and sf_private_key_path
    ), "Missing Snowflake env vars (require USER, ACCOUNT, and PRIVATE_KEY_PATH)."

    conn = None
    try:
        from cryptography.hazmat.primitives import serialization

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
        cur = conn.cursor()
        try:
            cur.execute("SELECT CURRENT_VERSION();")
            version = cur.fetchone()
            assert version and len(version[0]) > 0, "Snowflake connectivity check failed."
        finally:
            cur.close()
    finally:
        if conn is not None:
            conn.close()


