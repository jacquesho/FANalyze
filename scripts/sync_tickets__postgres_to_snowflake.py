#!/usr/bin/env python3
"""
Sync ticket sales data from Postgres to Snowflake
Handles incremental sync with status tracking
"""

import os
import sys
import psycopg2
from datetime import datetime
import logging
from pathlib import Path

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from api_config import get_snowflake_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_postgres_connection():
    """Get Postgres connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DATABASE", "fanalyze"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
        )
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to Postgres: {e}")


def add_sync_columns_if_needed(conn):
    """Add sync tracking columns to ticket_sales table if they don't exist"""

    cursor = conn.cursor()
    try:
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ticket_sales' 
            AND column_name IN ('sync_status', 'synced_at')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]

        # Add sync_status column if it doesn't exist
        if "sync_status" not in existing_columns:
            cursor.execute("""
                ALTER TABLE ticket_sales 
                ADD COLUMN sync_status VARCHAR(20) DEFAULT 'pending'
            """)
            logger.info("✅ Added sync_status column")

        # Add synced_at column if it doesn't exist
        if "synced_at" not in existing_columns:
            cursor.execute("""
                ALTER TABLE ticket_sales 
                ADD COLUMN synced_at TIMESTAMP
            """)
            logger.info("✅ Added synced_at column")

        conn.commit()

    except Exception as e:
        logger.error(f"❌ Error adding sync columns: {e}")
        raise
    finally:
        cursor.close()


def get_pending_records(conn):
    """Get records that need to be synced to Snowflake"""

    query = """
    SELECT 
        show_id,
        sale_date,
        tickets_sold,
        cumulative_tickets_sold,
        revenue,
        cumulative_revenue,
        sales_rate,
        days_until_show,
        created_at
    FROM ticket_sales 
    WHERE sync_status IN ('pending', 'updated')
    ORDER BY created_at
    """

    cursor = conn.cursor()
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        logger.info(f"📊 Found {len(records)} records pending sync")
        return records
    except Exception as e:
        logger.error(f"❌ Error fetching pending records: {e}")
        raise
    finally:
        cursor.close()


def create_snowflake_table_if_needed(snowflake_conn):
    """Create ticket_sales table in Snowflake if it doesn't exist"""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS FAN_RAW.TICKET_SALES (
        SHOW_ID VARCHAR(255) NOT NULL,
        SALE_DATE DATE NOT NULL,
        TICKETS_SOLD INTEGER NOT NULL,
        CUMULATIVE_TICKETS_SOLD INTEGER NOT NULL,
        REVENUE DECIMAL(10,2) NOT NULL,
        CUMULATIVE_REVENUE DECIMAL(10,2) NOT NULL,
        SALES_RATE DECIMAL(5,2) NOT NULL,
        DAYS_UNTIL_SHOW INTEGER NOT NULL,
        CREATED_AT TIMESTAMP_NTZ,
        SYNCED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        UNIQUE(SHOW_ID, SALE_DATE)
    );
    """

    cursor = snowflake_conn.cursor()
    try:
        cursor.execute(create_table_sql)
        snowflake_conn.commit()
        logger.info("✅ Snowflake ticket_sales table created/verified")
    except Exception as e:
        logger.error(f"❌ Error creating Snowflake table: {e}")
        raise
    finally:
        cursor.close()


def sync_records_to_snowflake(snowflake_conn, records):
    """Sync records from Postgres to Snowflake"""

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
                    record[0],  # show_id
                    record[1],  # sale_date
                    record[2],  # tickets_sold
                    record[3],  # cumulative_tickets_sold
                    record[4],  # revenue
                    record[5],  # cumulative_revenue
                    record[6],  # sales_rate
                    record[7],  # days_until_show
                    record[8],  # created_at
                    datetime.now(),  # synced_at
                )
            )

        # Insert/update data in Snowflake
        insert_sql = """
        INSERT INTO FAN_RAW.TICKET_SALES 
        (SHOW_ID, SALE_DATE, TICKETS_SOLD, CUMULATIVE_TICKETS_SOLD, REVENUE, 
         CUMULATIVE_REVENUE, SALES_RATE, DAYS_UNTIL_SHOW, CREATED_AT, SYNCED_AT)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (SHOW_ID, SALE_DATE) DO UPDATE SET
            TICKETS_SOLD = EXCLUDED.TICKETS_SOLD,
            CUMULATIVE_TICKETS_SOLD = EXCLUDED.CUMULATIVE_TICKETS_SOLD,
            REVENUE = EXCLUDED.REVENUE,
            CUMULATIVE_REVENUE = EXCLUDED.CUMULATIVE_REVENUE,
            SALES_RATE = EXCLUDED.SALES_RATE,
            DAYS_UNTIL_SHOW = EXCLUDED.DAYS_UNTIL_SHOW,
            SYNCED_AT = EXCLUDED.SYNCED_AT
        """

        cursor.executemany(insert_sql, data_tuples)
        snowflake_conn.commit()

        logger.info(f"✅ Successfully synced {len(records)} records to Snowflake")
        return True

    except Exception as e:
        logger.error(f"❌ Error syncing to Snowflake: {e}")
        snowflake_conn.rollback()
        return False
    finally:
        cursor.close()


def update_sync_status(conn, records, status):
    """Update sync status in Postgres for synced records"""

    if not records:
        return

    cursor = conn.cursor()
    try:
        # Update sync status for all synced records
        for record in records:
            cursor.execute(
                """
                UPDATE ticket_sales 
                SET sync_status = %s, synced_at = %s
                WHERE show_id = %s AND sale_date = %s
            """,
                (status, datetime.now(), record[0], record[1]),
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
    """Main function to sync ticket sales from Postgres to Snowflake"""

    logger.info("🔄 Starting Postgres to Snowflake sync...")

    postgres_conn = None
    snowflake_conn = None

    try:
        # Connect to Postgres
        logger.info("🔌 Connecting to Postgres...")
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
        snowflake_conn = get_snowflake_connection()

        # Create Snowflake table if needed
        create_snowflake_table_if_needed(snowflake_conn)

        # Sync records to Snowflake
        logger.info("📤 Syncing records to Snowflake...")
        sync_success = sync_records_to_snowflake(snowflake_conn, pending_records)

        if sync_success:
            # Update sync status in Postgres
            logger.info("📝 Updating sync status in Postgres...")
            update_sync_status(postgres_conn, pending_records, "synced")

            logger.info("🎉 Sync completed successfully!")
            logger.info(f"📊 Synced {len(pending_records)} records")
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
