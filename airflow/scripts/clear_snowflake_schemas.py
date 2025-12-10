#!/usr/bin/env python3
"""
Clear Snowflake Schemas Script
Clears all schemas/tables created by the batch pipeline for a clean state
"""

import os
import sys
import logging
from pathlib import Path

# Add config directory to path
# When running in Airflow container, config is mounted at /opt/airflow/project_config
if os.path.exists('/opt/airflow/project_config'):
    sys.path.append('/opt/airflow/project_config')
else:
    # Fallback for local development
    sys.path.append(str(Path(__file__).parent.parent.parent / "config"))

try:
    from api_config import get_snowflake_connection
except ImportError:
    print("Error: Could not import Snowflake configuration")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_snowflake_schemas():
    """Clear all schemas/tables created by the batch pipeline"""
    
    logger.info("🧹 Starting Snowflake schema cleanup...")
    
    # Get path to SQL file
    script_dir = Path(__file__).parent
    sql_file = script_dir / "clear_snowflake_schemas.sql"
    
    if not sql_file.exists():
        logger.error(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)
    
    # Read SQL file
    with open(sql_file, 'r') as f:
        sql_commands = f.read()
    
    # Connect to Snowflake
    conn = None
    try:
        logger.info("🔌 Connecting to Snowflake...")
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Execute SQL commands
        logger.info("🗑️  Executing cleanup SQL commands...")
        
        # Split by semicolon and execute each command
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        for command in commands:
            if command:
                try:
                    cursor.execute(command)
                    logger.info(f"✅ Executed: {command[:50]}...")
                except Exception as e:
                    # Log but continue - some commands may fail if objects don't exist
                    logger.warning(f"⚠️  Command failed (may be expected): {e}")
        
        conn.commit()
        logger.info("🎉 Snowflake schema cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_snowflake_schemas()

