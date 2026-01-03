#!/usr/bin/env python3
"""
Diagnostic script to check LangGraph PostgreSQL connection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (FANalyze_v2.0/.env)
# Script is in langgraph/scripts/, so go up 2 levels to project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parents[1]  # Go up 2 levels: scripts -> langgraph -> FANalyze_v2.0
env_path = project_root / ".env"

# Debug: show what path we're looking for
print(f"🔍 Looking for .env at: {env_path}")
print(f"   File exists: {env_path.exists()}")

if not env_path.exists():
    print(f"\n⚠️  .env file not found at expected location!")
    print(f"   Checked: {env_path}")
    print(f"   Current working directory: {Path.cwd()}")
    print(f"   Script location: {Path(__file__).resolve()}")

load_dotenv(dotenv_path=env_path, override=False)

print("🔍 LangGraph PostgreSQL Connection Diagnostic")
print("=" * 60)

# Check environment variables
required_vars = {
    "LANGGRAPH_POSTGRES_HOST": os.getenv("LANGGRAPH_POSTGRES_HOST"),
    "LANGGRAPH_POSTGRES_PORT": os.getenv("LANGGRAPH_POSTGRES_PORT"),
    "LANGGRAPH_POSTGRES_DB": os.getenv("LANGGRAPH_POSTGRES_DB"),
    "LANGGRAPH_POSTGRES_USER": os.getenv("LANGGRAPH_POSTGRES_USER"),
    "LANGGRAPH_POSTGRES_PASSWORD": os.getenv("LANGGRAPH_POSTGRES_PASSWORD"),
}

print("\n📋 Environment Variables:")
missing = []
for var, value in required_vars.items():
    if value:
        # Hide password
        display_value = "***" if "PASSWORD" in var else value
        print(f"   ✅ {var} = {display_value}")
    else:
        print(f"   ❌ {var} = (not set)")
        missing.append(var)

if missing:
    print(f"\n⚠️  Missing variables: {', '.join(missing)}")
    print("   Add these to your .env file")
else:
    print("\n✅ All environment variables are set")

# Try to import psycopg
print("\n📦 Checking psycopg library...")
try:
    import psycopg
    print("   ✅ psycopg is installed")
except ImportError:
    print("   ❌ psycopg is not installed")
    print("   Run: uv add psycopg")
    sys.exit(1)

# Try connection
if not missing:
    print("\n🔗 Testing connection...")
    try:
        db_uri = f"postgresql://{required_vars['LANGGRAPH_POSTGRES_USER']}:{required_vars['LANGGRAPH_POSTGRES_PASSWORD']}@{required_vars['LANGGRAPH_POSTGRES_HOST']}:{required_vars['LANGGRAPH_POSTGRES_PORT']}/{required_vars['LANGGRAPH_POSTGRES_DB']}"
        
        conn = psycopg.connect(
            db_uri,
            connect_timeout=3
        )
        
        # Test query
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"   ✅ Connected successfully!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            
            # Check if database exists
            cur.execute("SELECT current_database();")
            db_name = cur.fetchone()[0]
            print(f"   Current database: {db_name}")
            
            # Check if tables exist (from PostgresSaver.setup())
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'checkpoint%'
            """)
            tables = cur.fetchall()
            if tables:
                print(f"   ✅ LangGraph tables found: {len(tables)}")
                for table in tables:
                    print(f"      - {table[0]}")
            else:
                print("   ⚠️  No LangGraph tables found (run PostgresSaver.setup() on first use)")
        
        conn.close()
        print("\n✅ Connection test passed! Streamlit should be able to connect.")
        
    except psycopg.OperationalError as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure PostgreSQL container is running")
        print("   2. Check host/port are correct")
        print("   3. Run setup script: python langgraph/scripts/create_langgraph_service_user.py")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)

