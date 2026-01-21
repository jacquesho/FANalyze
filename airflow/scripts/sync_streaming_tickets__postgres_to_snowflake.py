#!/usr/bin/env python3
"""
Sync streaming ticket sales data from PostgreSQL staging.ticket_sales to Snowflake FAN_RAW.raw_tickets
Handles incremental sync with status tracking for real-time streaming data
"""

import os
import sys
import psycopg2
from datetime import datetime
import logging
from pathlib import Path

# Add config directory to path
# When running in Airflow container, config is mounted at /opt/airflow/project_config
if os.path.exists("/opt/airflow/project_config"):
    sys.path.append("/opt/airflow/project_config")
else:
    # Fallback for local development
    sys.path.append(str(Path(__file__).parent.parent / "config"))
from api_config import get_snowflake_connection

# Set up logging with unbuffered output for Airflow
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,  # Override any existing config
)
logger = logging.getLogger(__name__)
# Ensure logging flushes immediately
for handler in logger.handlers:
    handler.flush()
import sys

sys.stdout.flush()
sys.stderr.flush()


def get_postgres_connection():
    """Get Postgres connection using ingest service user credentials"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "kafka-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER_INGEST", "user_fanalyze_ingest"),
            password=os.getenv("POSTGRES_PASSWORD_INGEST", "fanalyze_ingest_password"),
            connect_timeout=10,  # 10 second connection timeout
        )
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to Postgres: {e}")


def add_sync_columns_if_needed(conn):
    """Add sync tracking columns to staging.ticket_sales table if they don't exist"""

    cursor = conn.cursor()
    try:
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'staging' 
            AND table_name = 'ticket_sales' 
            AND column_name IN ('sync_status', 'synced_at')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]

        # Add sync_status column if it doesn't exist
        if "sync_status" not in existing_columns:
            cursor.execute("""
                ALTER TABLE staging.ticket_sales 
                ADD COLUMN sync_status VARCHAR(20) DEFAULT 'pending'
            """)
            logger.info("✅ Added sync_status column to staging.ticket_sales")

        # Add synced_at column if it doesn't exist
        if "synced_at" not in existing_columns:
            cursor.execute("""
                ALTER TABLE staging.ticket_sales 
                ADD COLUMN synced_at TIMESTAMP
            """)
            logger.info("✅ Added synced_at column to staging.ticket_sales")

        conn.commit()

    except Exception as e:
        logger.error(f"❌ Error adding sync columns: {e}")
        # If it's a permission error, provide helpful message
        if "permission denied" in str(e).lower() or "must be owner" in str(e).lower():
            logger.error(
                "💡 Tip: Run 'GRANT ALL PRIVILEGES ON TABLE staging.ticket_sales TO service;' as postgres admin"
            )
        raise
    finally:
        cursor.close()


def get_pending_records(conn):
    """Get records from staging.ticket_sales that need to be synced to Snowflake"""

    query = """
    SELECT 
        id,
        timestamp,
        show_id,
        artist_name,
        venue_name,
        show_date,
        city_name,
        state_code,
        tickets_sold,
        cumulative_tickets_sold,
        revenue,
        cumulative_revenue,
        venue_capacity,
        sales_rate,
        days_until_show,
        artist_tier,
        average_ticket_price,
        created_at
    FROM staging.ticket_sales 
    WHERE sync_status IS NULL OR sync_status IN ('pending', 'failed')
    ORDER BY created_at
    """

    cursor = conn.cursor()
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        logger.info(
            f"📊 Found {len(records)} records pending sync from staging.ticket_sales"
        )
        return records
    except Exception as e:
        logger.error(f"❌ Error fetching pending records: {e}")
        raise
    finally:
        cursor.close()


def create_snowflake_table_if_needed(snowflake_conn):
    """Create FAN_RAW.raw_tickets table in Snowflake if it doesn't exist"""

    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS FAN_RAW;"

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS FAN_RAW.raw_tickets (
        id INTEGER NOT NULL,
        timestamp TIMESTAMP_TZ NOT NULL,
        show_id VARCHAR(255) NOT NULL,
        artist_name VARCHAR(255) NOT NULL,
        venue_name VARCHAR(255) NOT NULL,
        show_date DATE NOT NULL,
        city_name VARCHAR(255) NOT NULL,
        state_code VARCHAR(2) NOT NULL,
        tickets_sold INTEGER NOT NULL,
        cumulative_tickets_sold INTEGER NOT NULL,
        revenue DECIMAL(10,2) NOT NULL,
        cumulative_revenue DECIMAL(10,2) NOT NULL,
        venue_capacity INTEGER NOT NULL,
        sales_rate DECIMAL(5,2) NOT NULL,
        days_until_show INTEGER NOT NULL,
        artist_tier VARCHAR(50) NOT NULL,
        average_ticket_price DECIMAL(10,2) NOT NULL,
        created_at TIMESTAMP_TZ NOT NULL,
        synced_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
        PRIMARY KEY (id)
    );
    """

    cursor = snowflake_conn.cursor()
    try:
        # Create schema first
        cursor.execute(create_schema_sql)
        logger.info("✅ Created FAN_RAW schema")

        # Create table
        cursor.execute(create_table_sql)
        snowflake_conn.commit()
        logger.info("✅ Snowflake FAN_RAW.raw_tickets table created/verified")
    except Exception as e:
        logger.error(f"❌ Error creating Snowflake table: {e}")
        raise
    finally:
        cursor.close()


def sync_records_to_snowflake(snowflake_conn, records):
    """Sync records from PostgreSQL staging.ticket_sales to Snowflake FAN_RAW.raw_tickets"""

    if not records:
        logger.info("📊 No records to sync")
        return True

    cursor = snowflake_conn.cursor()
    try:
        # Prepare data for insertion
        data_tuples = []
        for record in records:
            data_tuples.append(
                (
                    record[0],  # id
                    record[1],  # timestamp
                    record[2],  # show_id
                    record[3],  # artist_name
                    record[4],  # venue_name
                    record[5],  # show_date
                    record[6],  # city_name
                    record[7],  # state_code
                    record[8],  # tickets_sold
                    record[9],  # cumulative_tickets_sold
                    record[10],  # revenue
                    record[11],  # cumulative_revenue
                    record[12],  # venue_capacity
                    record[13],  # sales_rate
                    record[14],  # days_until_show
                    record[15],  # artist_tier
                    record[16],  # average_ticket_price
                    record[17],  # created_at
                    datetime.now(),  # synced_at
                )
            )

        # Insert data in Snowflake
        insert_sql = """
        INSERT INTO FAN_RAW.raw_tickets 
        (id, timestamp, show_id, artist_name, venue_name, show_date, city_name, state_code,
         tickets_sold, cumulative_tickets_sold, revenue, cumulative_revenue, venue_capacity,
         sales_rate, days_until_show, artist_tier, average_ticket_price, created_at, synced_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.executemany(insert_sql, data_tuples)
        snowflake_conn.commit()

        logger.info(
            f"✅ Successfully synced {len(records)} records to Snowflake FAN_RAW.raw_tickets"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Error syncing to Snowflake: {e}")
        snowflake_conn.rollback()
        return False
    finally:
        cursor.close()


def update_sync_status(conn, records, status):
    """Update sync status in PostgreSQL staging.ticket_sales for synced records"""

    if not records:
        return

    cursor = conn.cursor()
    try:
        # Update sync status for all synced records
        for record in records:
            cursor.execute(
                """
                UPDATE staging.ticket_sales 
                SET sync_status = %s, synced_at = %s
                WHERE id = %s
            """,
                (status, datetime.now(), record[0]),
            )

        conn.commit()
        logger.info(f"✅ Updated sync status to '{status}' for {len(records)} records")

    except Exception as e:
        logger.error(f"❌ Error updating sync status: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()


def main():
    """Main function to sync streaming ticket sales from PostgreSQL to Snowflake"""
    import sys

    logger.info("🔄 Starting streaming ticket sync from PostgreSQL to Snowflake...")
    sys.stdout.flush()  # Ensure output appears immediately

    postgres_conn = None
    snowflake_conn = None

    try:
        # Connect to PostgreSQL
        logger.info("🔌 Connecting to PostgreSQL...")
        sys.stdout.flush()
        postgres_conn = get_postgres_connection()

        # Add sync columns if needed
        add_sync_columns_if_needed(postgres_conn)

        # Get pending records
        pending_records = get_pending_records(postgres_conn)

        if not pending_records:
            logger.info("📊 No records pending sync")
            return

        # Connect to Snowflake
        logger.info("🔌 Connecting to Snowflake...")
        sys.stdout.flush()
        snowflake_conn = get_snowflake_connection()

        # Create Snowflake table if needed
        create_snowflake_table_if_needed(snowflake_conn)

        # Sync records to Snowflake
        logger.info("📤 Syncing records to Snowflake FAN_RAW.raw_tickets...")
        sys.stdout.flush()
        sync_success = sync_records_to_snowflake(snowflake_conn, pending_records)

        if sync_success:
            # Update sync status in PostgreSQL
            logger.info("📝 Updating sync status in PostgreSQL...")
            update_sync_status(postgres_conn, pending_records, "synced")

            logger.info("🎉 Sync completed successfully!")
            logger.info(
                f"📊 Synced {len(pending_records)} records from staging.ticket_sales to FAN_RAW.raw_tickets"
            )
        else:
            # Mark records as failed
            update_sync_status(postgres_conn, pending_records, "failed")
            logger.error("❌ Sync failed - records marked as failed")

    except Exception as e:
        logger.error(f"❌ Error during sync: {e}")
        raise
    finally:
        if postgres_conn:
            postgres_conn.close()
        if snowflake_conn:
            snowflake_conn.close()


if __name__ == "__main__":
    main()
