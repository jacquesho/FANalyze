#!/usr/bin/env python3
"""
CI Database Manager - Create and drop FANALYZE_CI database for CI testing
"""

import os
import sys
import snowflake.connector
from cryptography.hazmat.primitives import serialization


def get_snowflake_connection():
    """Get Snowflake connection using environment variables"""
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH", ".secrets/rsa_key.p8")
    key_pwd = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD")

    if not os.path.exists(key_path):
        raise Exception(f"Private key file not found: {key_path}")

    with open(key_path, "rb") as key_file:
        private_key_pem = key_file.read()

    # Load private key
    if key_pwd:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=key_pwd.encode() if isinstance(key_pwd, str) else key_pwd,
        )
    else:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
        )

    # Convert to DER format
    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        private_key=private_key_der,
        authenticator="snowflake",
    )
    return conn


def create_ci_database():
    """Create FANALYZE_CI database with required schemas"""
    print("🔧 Creating FANALYZE_CI database...")
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        # Drop existing database if it exists (clean slate)
        cursor.execute("DROP DATABASE IF EXISTS FANALYZE_CI CASCADE")
        print("✅ Dropped existing FANALYZE_CI database (if existed)")

        # Create database
        cursor.execute("CREATE DATABASE FANALYZE_CI")
        print("✅ Created FANALYZE_CI database")

        # Use the database
        cursor.execute("USE DATABASE FANALYZE_CI")

        # Create required schemas
        # Note: dbt will create FAN_STAGING, FAN_INTERMEDIATE, FAN_MARTS automatically
        # We only need to create FAN_RAW here
        schemas = ["FAN_RAW"]
        for schema in schemas:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            print(f"✅ Created schema {schema}")
        # dbt will create FAN_STAGING, FAN_INTERMEDIATE, FAN_MARTS when models run

        cursor.close()
        conn.close()
        print("🎉 FANALYZE_CI database setup complete!")
        return True

    except Exception as e:
        print(f"❌ Error creating CI database: {e}")
        cursor.close()
        conn.close()
        return False


def drop_ci_database():
    """Drop FANALYZE_CI database"""
    print("🗑️  Dropping FANALYZE_CI database...")
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DROP DATABASE IF EXISTS FANALYZE_CI CASCADE")
        cursor.close()
        conn.close()
        print("✅ Dropped FANALYZE_CI database")
        return True

    except Exception as e:
        print(f"❌ Error dropping CI database: {e}")
        cursor.close()
        conn.close()
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python ci_database_manager.py [create|drop]")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "create":
        success = create_ci_database()
        sys.exit(0 if success else 1)
    elif action == "drop":
        success = drop_ci_database()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown action: {action}. Use 'create' or 'drop'")
        sys.exit(1)


if __name__ == "__main__":
    main()
