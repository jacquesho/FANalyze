#!/usr/bin/env python3
"""
Script to clear Snowflake schemas/tables before running the batch pipeline
This ensures a clean state for testing
"""

import os
import sys
import snowflake.connector

# Add the config directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from api_config import get_snowflake_connection
except ImportError:
    print("Error: Could not import Snowflake configuration")
    sys.exit(1)

def clear_snowflake_schemas():
    """Clear all schemas/tables created by the batch pipeline"""
    
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        print("🗑️  Clearing Snowflake schemas/tables...")
        
        # Clear FAN_RAW schema tables
        print("  - Clearing FAN_RAW.SHOWS_HIS...")
        cursor.execute("TRUNCATE TABLE IF EXISTS FAN_RAW.SHOWS_HIS")
        
        print("  - Clearing FAN_RAW.SHOWS_FUTURE...")
        cursor.execute("TRUNCATE TABLE IF EXISTS FAN_RAW.SHOWS_FUTURE")
        
        # Drop dbt schemas
        print("  - Dropping staging schema...")
        cursor.execute("DROP SCHEMA IF EXISTS staging CASCADE")
        
        print("  - Dropping intermediate schema...")
        cursor.execute("DROP SCHEMA IF EXISTS intermediate CASCADE")
        
        print("  - Dropping marts schema...")
        cursor.execute("DROP SCHEMA IF EXISTS marts CASCADE")
        
        conn.commit()
        print("✅ Successfully cleared all schemas/tables!")
        print("\n📝 Note: FAN_RAW schema and tables will be recreated by the ingestion script")
        print("   The dbt schemas will be recreated by dbt run")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing schemas: {e}")
        return False

if __name__ == "__main__":
    success = clear_snowflake_schemas()
    sys.exit(0 if success else 1)


