#!/usr/bin/env python3
"""
Test: PostgreSQL to Snowflake Connection Testing
"""

import os
import sys
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(project_root, ".env"), override=False)

console = Console()


def test_postgres_connection():
    """Test PostgreSQL connection."""
    try:
        import psycopg
        
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        dbname = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER_INGEST")
        password = os.getenv("POSTGRES_PASSWORD_INGEST")

        if not all([host, port, dbname, user, password]):
            console.print("❌ Missing required PostgreSQL environment variables for ingest user", style="red")
            return False

        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM staging.test_ingest")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        console.print(f"✅ PostgreSQL connection successful - {count} records in staging.test_ingest", style="green")
        return True
        
    except (psycopg.Error, ConnectionError) as e:
        console.print(f"❌ PostgreSQL connection failed: {e}", style="red")
        return False


def test_snowflake_connection():
    """Test Snowflake connection."""
    try:
        import snowflake.connector
        from cryptography.hazmat.primitives import serialization
        
        sf_user = os.getenv("SNOWFLAKE_USER")
        sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
        sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        sf_database = os.getenv("SNOWFLAKE_DATABASE")
        sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        sf_role = os.getenv("SNOWFLAKE_ROLE")
        sf_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

        if not all([sf_user, sf_account, sf_private_key_path]):
            console.print("❌ Missing required Snowflake environment variables", style="red")
            return False

        # Load private key
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
        
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        console.print(f"✅ Snowflake connection successful - Version: {version}", style="green")
        return True
        
    except (snowflake.connector.Error, FileNotFoundError, ValueError) as e:
        console.print(f"❌ Snowflake connection failed: {e}", style="red")
        return False


def test_pg_to_sf_connections():
    """Test both PostgreSQL and Snowflake connections."""
    console.print("🔍 Testing PostgreSQL to Snowflake Connections", style="bold blue")
    console.print("=" * 50)
    
    # Test PostgreSQL
    console.print("\n1️⃣ Testing PostgreSQL connection", style="blue")
    pg_success = test_postgres_connection()
    
    # Test Snowflake
    console.print("\n2️⃣ Testing Snowflake connection", style="blue")
    sf_success = test_snowflake_connection()
    
    # Summary
    console.print("\n📊 Connection Test Summary:", style="bold")
    console.print(f"   PostgreSQL: {'✅ Success' if pg_success else '❌ Failed'}")
    console.print(f"   Snowflake: {'✅ Success' if sf_success else '❌ Failed'}")
    
    if pg_success and sf_success:
        console.print("\n🚀 Both connections successful! Ready to run data transfer test.", style="green")
        console.print("   Run: python tests/DB_tests/test_pg_to_sf_transfer.py", style="cyan")
        return True
    else:
        console.print("\n❌ Connection issues detected. Please check your environment variables.", style="red")
        return False


if __name__ == "__main__":
    success = test_pg_to_sf_connections()
    sys.exit(0 if success else 1)
