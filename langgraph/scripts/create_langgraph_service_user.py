#!/usr/bin/env python3
"""
Create LangGraph PostgreSQL Service User and Database
Creates the 'langgraph_service' user and 'langgraph_memory' database for LangGraph checkpointing.

This script creates a NEW database on your EXISTING PostgreSQL server (same server as FANalyze).
It uses your admin credentials (POSTGRES_USER/POSTGRES_PASSWORD) to create:
- A new database: langgraph_memory
- A new service user: langgraph_service (with limited privileges)

The langgraph_memory database will be on the same PostgreSQL instance as your other databases.
You can verify it exists by connecting with your admin credentials and listing databases.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load .env file from project root (FANalyze_v2.0/.env)
# Script is in langgraph/scripts/, so go up 2 levels to project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parents[1]  # Go up 2 levels: scripts -> langgraph -> FANalyze_v2.0
load_dotenv(dotenv_path=project_root / ".env", override=False)

def get_admin_connection(database='postgres'):
    """Get PostgreSQL admin connection using environment variables from .env"""
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    
    # Validate required environment variables
    if not all([host, port, user, password]):
        missing = []
        if not host:
            missing.append('POSTGRES_HOST')
        if not port:
            missing.append('POSTGRES_PORT')
        if not user:
            missing.append('POSTGRES_USER')
        if not password:
            missing.append('POSTGRES_PASSWORD')
        
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("\n💡 Please set these in your .env file:")
        print("   - POSTGRES_HOST (e.g., localhost or kafka-postgres)")
        print("   - POSTGRES_PORT (e.g., 5432)")
        print("   - POSTGRES_USER (your PostgreSQL admin username)")
        print("   - POSTGRES_PASSWORD (your PostgreSQL admin password)")
        return None
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print(f"\n💡 Attempted connection to: {user}@{host}:{port}/{database}")
        print("\n💡 Make sure PostgreSQL is running and credentials in .env are correct.")
        return None

def create_langgraph_setup():
    """Create LangGraph database and service user"""
    # Connect to postgres database first
    conn = get_admin_connection('postgres')
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create langgraph_memory database
        print("📦 Creating langgraph_memory database...")
        cursor.execute("""
            SELECT 1 FROM pg_database WHERE datname = 'langgraph_memory'
        """)
        if cursor.fetchone():
            print("   Database 'langgraph_memory' already exists")
        else:
            cursor.execute("CREATE DATABASE langgraph_memory;")
            print("   ✅ Database 'langgraph_memory' created successfully")
        
        # Create the langgraph_service user
        print("👤 Creating langgraph_service user...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'langgraph_service') THEN
                    CREATE USER langgraph_service WITH PASSWORD 'langgraph_service_password' LOGIN;
                    RAISE NOTICE 'User "langgraph_service" created successfully';
                ELSE
                    ALTER USER langgraph_service WITH PASSWORD 'langgraph_service_password' LOGIN;
                    RAISE NOTICE 'User "langgraph_service" already exists - password updated';
                END IF;
            END
            $$;
        """)
        
        # Grant database-level privileges
        print("🔐 Granting database privileges...")
        cursor.execute("GRANT CONNECT ON DATABASE langgraph_memory TO langgraph_service;")
        cursor.execute("GRANT CREATE ON DATABASE langgraph_memory TO langgraph_service;")
        
        cursor.close()
        conn.close()
        
        # Now connect to langgraph_memory database to grant schema privileges
        print("🔗 Connecting to langgraph_memory database...")
        conn_langgraph = get_admin_connection('langgraph_memory')
        if not conn_langgraph:
            return False
        
        cursor_langgraph = conn_langgraph.cursor()
        
        # Grant schema privileges
        print("🔐 Granting schema privileges...")
        cursor_langgraph.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO langgraph_service;")
        cursor_langgraph.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO langgraph_service;")
        cursor_langgraph.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO langgraph_service;")
        
        # Grant privileges on future tables/sequences (for PostgresSaver.setup())
        cursor_langgraph.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO langgraph_service;")
        cursor_langgraph.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO langgraph_service;")
        
        # Get actual connection details for display
        actual_host = os.getenv('POSTGRES_HOST')
        actual_port = os.getenv('POSTGRES_PORT')
        
        print("✅ LangGraph setup completed successfully!")
        print("\n📋 Configuration:")
        print("   Database: langgraph_memory")
        print("   Username: langgraph_service")
        print("   Password: langgraph_service_password")
        print(f"   Host: {actual_host} (same PostgreSQL server as FANalyze)")
        print(f"   Port: {actual_port}")
        print("\n💡 Update your .env file with:")
        print(f"   LANGGRAPH_POSTGRES_HOST={actual_host}")
        print(f"   LANGGRAPH_POSTGRES_PORT={actual_port}")
        print("   LANGGRAPH_POSTGRES_DB=langgraph_memory")
        print("   LANGGRAPH_POSTGRES_USER=langgraph_service")
        print("   LANGGRAPH_POSTGRES_PASSWORD=langgraph_service_password")
        print("\n📝 Note: langgraph_memory is a new database on your existing PostgreSQL server.")
        print("   You can connect to it using your admin credentials to verify it was created.")
        
        cursor_langgraph.close()
        conn_langgraph.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating LangGraph setup: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔄 Creating LangGraph PostgreSQL service user and database...")
    print("=" * 60)
    success = create_langgraph_setup()
    sys.exit(0 if success else 1)

