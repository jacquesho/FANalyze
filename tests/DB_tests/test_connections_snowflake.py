import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env() -> None:
    # Load .env explicitly from project root (FANalyze_v2.0/.env), regardless of CWD
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=project_root / ".env", override=False)


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

    assert sf_user and sf_account and sf_private_key_path, (
        "Missing Snowflake env vars (require USER, ACCOUNT, and PRIVATE_KEY_PATH)."
    )

    # Resolve relative paths relative to project root (same as config/api_config.py logic)
    if not os.path.isabs(sf_private_key_path):
        project_root = Path(__file__).resolve().parents[2]
        # Remove "./" prefix if present, but preserve ".secrets" (hidden directory)
        if sf_private_key_path.startswith("./"):
            normalized_path = sf_private_key_path[2:]  # Remove "./" prefix only
        else:
            normalized_path = sf_private_key_path
        sf_private_key_path = os.path.join(str(project_root), normalized_path)

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
            assert version and len(version[0]) > 0, (
                "Snowflake connectivity check failed."
            )
        finally:
            cur.close()
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    print("🔍 Testing Snowflake Connection...")
    print("=" * 50)

    try:
        _load_env()

        import snowflake.connector
        from cryptography.hazmat.primitives import serialization

        # Get environment variables
        sf_user = os.getenv("SNOWFLAKE_USER")
        sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
        sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        sf_database = os.getenv("SNOWFLAKE_DATABASE")
        sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        sf_role = os.getenv("SNOWFLAKE_ROLE")
        sf_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

        # Resolve relative paths relative to project root (same as config/api_config.py logic)
        if sf_private_key_path and not os.path.isabs(sf_private_key_path):
            project_root = Path(__file__).resolve().parents[2]
            # Remove "./" prefix if present, but preserve ".secrets" (hidden directory)
            if sf_private_key_path.startswith("./"):
                normalized_path = sf_private_key_path[2:]  # Remove "./" prefix only
            else:
                normalized_path = sf_private_key_path
            sf_private_key_path = os.path.join(str(project_root), normalized_path)

        # Check required variables
        print("📋 Configuration:")
        print(f"   User: {sf_user}")
        print(f"   Account: {sf_account}")
        if sf_account:
            if "." not in sf_account:
                print("   ⚠️  WARNING: Account identifier missing region suffix!")
                print(
                    f"      Expected format: {sf_account}.ap-southeast-1 (or your region)"
                )
            elif "_" in sf_account.split(".")[-1] or any(
                c.isupper() for c in sf_account.split(".")[-1] if "." in sf_account
            ):
                print("   ⚠️  WARNING: Region format may be incorrect!")
                print(f"      Current: {sf_account}")
                print(
                    f"      Should be: {sf_account.split('.')[0]}.ap-southeast-1 (lowercase, hyphens)"
                )
        print(f"   Warehouse: {sf_warehouse}")
        print(f"   Database: {sf_database}")
        print(f"   Schema: {sf_schema}")
        print(f"   Role: {sf_role}")
        print(f"   Key Path: {sf_private_key_path}")
        print()

        if not (sf_user and sf_account and sf_private_key_path):
            print("❌ Missing required Snowflake environment variables:")
            if not sf_user:
                print("   - SNOWFLAKE_USER")
            if not sf_account:
                print("   - SNOWFLAKE_ACCOUNT")
            if not sf_private_key_path:
                print("   - SNOWFLAKE_PRIVATE_KEY_PATH")
            print(
                "\n⚠️  Please check your .env file for missing Snowflake configuration."
            )
            exit(1)

        # Check if key file exists
        if not os.path.exists(sf_private_key_path):
            print(f"❌ Private key file not found: {sf_private_key_path}")
            print(f"   (Resolved from: {os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH')})")
            exit(1)

        print("🔑 Loading private key...")
        with open(sf_private_key_path, "rb") as f:
            private_key_pem = f.read()

        # Load and convert to DER format (same as api_config.py)
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
        )

        # Convert to DER format for Snowflake connector
        private_key_der = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Normalize account identifier to lowercase (Snowflake requires lowercase regions)
        if sf_account and "." in sf_account:
            account_parts = sf_account.split(".", 1)
            if len(account_parts) == 2:
                account_locator, region = account_parts
                # Convert region to lowercase with hyphens
                normalized_region = region.lower().replace("_", "-")
                normalized_account = f"{account_locator}.{normalized_region}"
                if normalized_account != sf_account:
                    print("   🔧 Normalizing account identifier:")
                    print(f"      From: {sf_account}")
                    print(f"      To:   {normalized_account}")
                    sf_account = normalized_account

        print("🔌 Connecting to Snowflake...")
        print(f"   Attempting connection to: {sf_account}")
        print(
            f"   Full connection URL would be: https://{sf_account}.snowflakecomputing.com"
        )

        # Try connection with DER format key and authenticator
        try:
            conn = snowflake.connector.connect(
                user=sf_user,
                account=sf_account,
                warehouse=sf_warehouse,
                database=sf_database,
                schema=sf_schema,
                role=sf_role,
                private_key=private_key_der,
                authenticator="snowflake",
            )
        except Exception as conn_error:
            # If connection fails with 404, try without warehouse/database/schema/role
            # (these aren't required for initial connection)
            if "404" in str(conn_error) or "Not Found" in str(conn_error):
                print("   ⚠️  Initial connection failed, trying minimal connection...")
                conn = snowflake.connector.connect(
                    user=sf_user,
                    account=sf_account,
                    private_key=private_key_der,
                    authenticator="snowflake",
                )
            else:
                raise

        print("✅ Connected successfully!")
        print()

        # Test queries
        cur = conn.cursor()
        try:
            # Get current user and role
            cur.execute(
                "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
            )
            user, role, wh, db, schema = cur.fetchone()
            print(f"👤 Current User: {user}")
            print(f"🎭 Current Role: {role}")
            print(f"🏭 Current Warehouse: {wh}")
            print(f"💾 Current Database: {db}")
            print(f"📁 Current Schema: {schema}")
            print()

            # Get Snowflake version
            cur.execute("SELECT CURRENT_VERSION()")
            version = cur.fetchone()[0]
            print(f"❄️  Snowflake Version: {version}")
            print()

            print("=" * 50)
            print("✅ All tests passed! Connection is working correctly.")

        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        exit(1)
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. USER_SVC uses key-pair authentication - NO PASSWORD needed!")

        if "404" in error_msg or "Not Found" in error_msg:
            print("   2. ⚠️  404 Error - Account identifier is incorrect:")
            print("      This means Snowflake can't find your account at that URL.")
            print("      Steps to fix:")
            print("      a) Log into Snowsight and check the URL:")
            print("         - Look for: https://[account].snowflakecomputing.com")
            print("         - Or: https://app.snowflake.com/[region]/[account]")
            print("      b) Run in Snowflake SQL:")
            print("         SELECT CURRENT_ACCOUNT(), CURRENT_REGION();")
            print("      c) Try these formats in your .env:")
            print("         - Just account: SNOWFLAKE_ACCOUNT=FE23702")
            print("         - With region: SNOWFLAKE_ACCOUNT=FE23702.ap-southeast-1")
            print(
                "         - Organization format: SNOWFLAKE_ACCOUNT=orgname-accountname"
            )
            print(
                "      d) Verify account exists - check you're using the right account!"
            )

        print("   3. Verify your public key fingerprint matches:")
        print("      - In Snowflake: DESC USER USER_SVC;")
        print(
            "      - Local key: openssl rsa -pubin -in .secrets/rsa_key.pub -outform DER | openssl dgst -sha256 -binary | openssl enc -base64"
        )
        print("   4. Check that USER_SVC has ROLE_ETL granted:")
        print("      SHOW GRANTS TO USER USER_SVC;")
        print("   5. Verify warehouse exists and is accessible:")
        print("      SHOW WAREHOUSES LIKE 'WH_FANALYZE';")
        exit(1)
