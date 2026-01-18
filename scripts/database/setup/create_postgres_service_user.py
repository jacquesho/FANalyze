#!/usr/bin/env python3
"""
Create PostgreSQL Service User
Creates the 'service' user with password 'airflow' for Airflow and other service connections
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_admin_connection():
    """Get PostgreSQL admin connection using environment variables or defaults"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "kafka-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n💡 Make sure PostgreSQL is running and credentials are correct.")
        print("   Check your .env file for POSTGRES_USER and POSTGRES_PASSWORD")
        return None


def create_service_user():
    """Create service user with password 'airflow'"""
    conn = get_admin_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Create the service user
        print("👤 Creating service user...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service') THEN
                    CREATE USER service WITH PASSWORD 'airflow' LOGIN;
                    RAISE NOTICE 'User "service" created successfully';
                ELSE
                    ALTER USER service WITH PASSWORD 'airflow' LOGIN;
                    RAISE NOTICE 'User "service" already exists - password updated';
                END IF;
            END
            $$;
        """)

        # Create staging schema if it doesn't exist
        print("📁 Ensuring staging schema exists...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")

        # Grant privileges on staging schema
        print("🔐 Granting privileges on staging schema...")
        cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA staging TO service;")
        cursor.execute(
            "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO service;"
        )
        cursor.execute(
            "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO service;"
        )

        # Grant privileges on future tables
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO service;"
        )
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON SEQUENCES TO service;"
        )

        print("✅ Service user 'service' created/updated successfully!")
        print("   Username: service")
        print("   Password: airflow")
        print("\n💡 Update your .env file with:")
        print("   POSTGRES_USER_INGEST=service")
        print("   POSTGRES_PASSWORD_INGEST=airflow")

        return True

    except Exception as e:
        print(f"❌ Error creating service user: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("🔄 Creating PostgreSQL service user...")
    success = create_service_user()
    sys.exit(0 if success else 1)
