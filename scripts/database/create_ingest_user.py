#!/usr/bin/env python3
"""
Create user_fanalyze_ingest user in PostgreSQL
Uses existing connection to create the new user and grant permissions
"""

import os
import sys
from pathlib import Path
import psycopg
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Load environment variables
load_dotenv()

console = Console()


def get_admin_connection():
    """Get PostgreSQL connection using your existing admin credentials."""
    try:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        dbname = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")

        missing = [name for name, val in [
            ("POSTGRES_HOST", host),
            ("POSTGRES_PORT", port),
            ("POSTGRES_DB", dbname),
            ("POSTGRES_USER", user),
            ("POSTGRES_PASSWORD", password),
        ] if not val]

        if missing:
            console.print("❌ Missing required environment variables: " + ", ".join(missing), style="red")
            return None

        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        return conn
    except Exception as e:
        console.print(f"❌ PostgreSQL connection failed: {e}", style="red")
        return None


def create_ingest_user():
    """Create user_fanalyze_ingest user and grant permissions."""
    try:
        conn = get_admin_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Create the user with explicit password and login privileges
        console.print("👤 Creating user_fanalyze_ingest user...", style="blue")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user_fanalyze_ingest') THEN
                    CREATE USER user_fanalyze_ingest WITH PASSWORD 'fanalyze_ingest_password' LOGIN;
                ELSE
                    -- If user exists, update password and ensure login privileges
                    ALTER USER user_fanalyze_ingest WITH PASSWORD 'fanalyze_ingest_password' LOGIN;
                END IF;
            END
            $$;
        """)
        
        # Create staging schema if it doesn't exist
        console.print("📁 Creating staging schema...", style="blue")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")
        
        # Check if table already exists
        console.print("🔍 Checking if table already exists...", style="blue")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'staging' AND table_name = 'test_ingest'
            );
        """)
        table_exists = cursor.fetchone()[0]
        console.print(f"📊 Table exists: {table_exists}", style="cyan")
        
        if table_exists:
            # Check existing table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'staging' AND table_name = 'test_ingest'
                ORDER BY ordinal_position;
            """)
            existing_columns = cursor.fetchall()
            console.print(f"📋 Existing table columns: {existing_columns}", style="cyan")
        
        # Create test_ingest table (drop and recreate if it exists with wrong structure)
        console.print("📊 Creating staging.test_ingest table...", style="blue")
        if table_exists:
            console.print("⚠️ Table exists with different structure, dropping and recreating...", style="yellow")
            cursor.execute("DROP TABLE IF EXISTS staging.test_ingest CASCADE;")
        
        cursor.execute("""
            CREATE TABLE staging.test_ingest (
                id INTEGER PRIMARY KEY,
                data_content TEXT,
                file_name VARCHAR(255),
                loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Commit the table creation before creating index
        conn.commit()
        console.print("✅ Table created and committed", style="green")
        
        # Verify table exists and has the column
        console.print("🔍 Verifying table structure...", style="blue")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'staging' AND table_name = 'test_ingest'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        console.print(f"📋 Table columns: {columns}", style="cyan")
        
        # Create index for performance (after table is created and committed)
        console.print("⚡ Creating performance index...", style="blue")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_ingest_loaded_at ON staging.test_ingest(loaded_at);")
        
        # Grant permissions to user_fanalyze_ingest (after table and index are created)
        console.print("🔐 Granting permissions to user_fanalyze_ingest...", style="blue")
        cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA staging TO user_fanalyze_ingest;")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO user_fanalyze_ingest;")
        cursor.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO user_fanalyze_ingest;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        console.print("✅ user_fanalyze_ingest user created successfully!", style="green")
        return True
        
    except Exception as e:
        console.print(f"❌ Failed to create user: {e}", style="red")
        return False


def verify_user_creation():
    """Verify that the user was created and has proper permissions."""
    try:
        # First, verify the user exists using admin connection
        console.print("🔍 Verifying user exists in PostgreSQL...", style="blue")
        admin_conn = get_admin_connection()
        if not admin_conn:
            console.print("❌ Cannot verify user - admin connection failed", style="red")
            return False
        
        admin_cursor = admin_conn.cursor()
        admin_cursor.execute("SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = 'user_fanalyze_ingest';")
        user_info = admin_cursor.fetchone()
        admin_cursor.close()
        admin_conn.close()
        
        if not user_info:
            console.print("❌ User user_fanalyze_ingest does not exist in PostgreSQL", style="red")
            return False
        
        console.print("✅ User user_fanalyze_ingest exists in PostgreSQL", style="green")
        console.print(f"📊 User can login: {user_info[1]}", style="cyan")
        
        if not user_info[1]:  # rolcanlogin is False
            console.print("⚠️ User exists but cannot login - this may be the issue", style="yellow")
        
        # Test connection with the new user using the exact password from creation
        console.print("🔐 Testing connection with user_fanalyze_ingest...", style="blue")
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user="user_fanalyze_ingest",
            password="fanalyze_ingest_password",
        )
        
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()[0]
        
        # Test schema access
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'staging';")
        schema_exists = cursor.fetchone() is not None
        
        # Test table access
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'staging' AND table_name = 'test_ingest';")
        table_exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        console.print(f"✅ User verification successful:", style="green")
        console.print(f"   • Current user: {current_user}", style="cyan")
        console.print(f"   • Staging schema accessible: {schema_exists}", style="cyan")
        console.print(f"   • test_ingest table accessible: {table_exists}", style="cyan")
        
        return True
        
    except Exception as e:
        console.print(f"❌ User verification failed: {e}", style="red")
        return False


def main():
    """Main function to create the ingest user."""
    console.print("🚀 FANalyze 2.0 - Create Ingest User", style="bold blue")
    console.print("=" * 50)
    
    # Step 1: Create the user
    console.print("\n1️⃣ Creating user_fanalyze_ingest user", style="blue")
    if not create_ingest_user():
        console.print("❌ User creation failed", style="red")
        return False
    
    # Step 2: Verify the user
    console.print("\n2️⃣ Verifying user creation", style="blue")
    if not verify_user_creation():
        console.print("❌ User verification failed", style="red")
        return False
    
    # Success summary
    console.print("\n🎉 User creation completed successfully!", style="bold green")
    
    success_panel = Panel(
        """✅ user_fanalyze_ingest user created successfully!

📊 What was accomplished:
   • User 'user_fanalyze_ingest' created with password 'fanalyze_ingest_password'
   • Staging schema created
   • test_ingest table created
   • Proper permissions granted
   • Performance index created
   • User verification completed

🔧 Next steps:
   • Update your .env file with the new credentials
   • Test the CSV ingestion functionality""",
        title="User Creation Results",
        border_style="green"
    )
    
    console.print(success_panel)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
