#!/usr/bin/env python3
"""
Clear Snowflake schemas script
Executes SQL commands to truncate raw tables and drop dbt-created schemas
"""

import os
import sys
import logging
from pathlib import Path

# Add config directory to path
# When running in Airflow container, config is mounted at /opt/airflow/project_config
if os.path.exists("/opt/airflow/project_config"):
    sys.path.append("/opt/airflow/project_config")
else:
    # Fallback for local development
    sys.path.append(str(Path(__file__).parent.parent / "config"))

try:
    from api_config import get_snowflake_connection
except ImportError:
    print("Error: Could not import Snowflake configuration")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def execute_sql_file(conn, sql_file_path):
    """Execute SQL commands from a file"""
    try:
        with open(sql_file_path, "r") as f:
            sql_content = f.read()

        # Split SQL statements by semicolon
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        cursor = conn.cursor()
        for statement in statements:
            if statement and not statement.startswith("--"):
                try:
                    logger.info(f"Executing: {statement[:100]}...")
                    cursor.execute(statement)
                    logger.info("✓ Executed successfully")
                except Exception as e:
                    # Log but continue - some statements may fail if objects don't exist
                    logger.warning(f"Statement failed (may be expected): {e}")

        conn.commit()
        cursor.close()
        logger.info("✓ All SQL statements executed")
        return True

    except Exception as e:
        logger.error(f"Error executing SQL file: {e}")
        return False


def main():
    """Main function to clear Snowflake schemas"""
    # Get SQL file path
    script_dir = Path(__file__).parent
    sql_file_path = script_dir / "clear_snowflake_schemas.sql"

    if not sql_file_path.exists():
        logger.error(f"SQL file not found: {sql_file_path}")
        return False

    # Connect to Snowflake
    try:
        conn = get_snowflake_connection()
        logger.info("Connected to Snowflake successfully")
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {e}")
        return False

    try:
        # Execute SQL file
        success = execute_sql_file(conn, sql_file_path)
        if success:
            logger.info("✅ Successfully cleared Snowflake schemas")
        else:
            logger.error("❌ Failed to clear Snowflake schemas")
        return success
    finally:
        conn.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
