#!/usr/bin/env python3
"""
Transfer ticket sales data from Postgres to Snowflake
"""

import os
import sys
import pandas as pd
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from api_config import get_snowflake_connection


class PostgresToSnowflake:
    def __init__(self, postgres_config, snowflake_conn):
        """Initialize connections"""
        self.pg_conn = psycopg2.connect(**postgres_config)
        self.sf_conn = snowflake_conn

    def get_postgres_data(self, limit=None):
        """Get ticket sales data from Postgres"""

        query = """
        SELECT 
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
        FROM ticket_sales
        ORDER BY timestamp
        """

        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql(query, self.pg_conn)
        return df

    def create_snowflake_table(self):
        """Create the ticket_sales table in Snowflake"""

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS fan_staging.ticket_sales_stream (
            id INTEGER AUTOINCREMENT PRIMARY KEY,
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
            created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
        );
        """

        cursor = self.sf_conn.cursor()
        cursor.execute(create_table_sql)
        cursor.close()
        print("✅ Snowflake table created/verified")

    def transfer_data(self, batch_size=1000):
        """Transfer data from Postgres to Snowflake"""

        print("📊 Getting data from Postgres...")
        df = self.get_postgres_data()

        if df.empty:
            print("❌ No data found in Postgres")
            return

        print(f"📈 Found {len(df)} records to transfer")

        # Create Snowflake table
        self.create_snowflake_table()

        # Prepare data for Snowflake
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["show_date"] = pd.to_datetime(df["show_date"]).dt.date
        df["created_at"] = pd.to_datetime(df["created_at"])

        # Transfer in batches
        total_batches = (len(df) + batch_size - 1) // batch_size

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            print(
                f"📤 Transferring batch {batch_num}/{total_batches} ({len(batch)} records)..."
            )

            # Write to Snowflake
            batch.to_sql(
                "ticket_sales_stream",
                self.sf_conn,
                schema="fan_staging",
                if_exists="append",
                index=False,
                method="multi",
            )

        print("✅ Data transfer complete!")

        # Show summary
        self.show_summary()

    def show_summary(self):
        """Show summary of transferred data"""

        summary_sql = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT show_id) as unique_shows,
            SUM(tickets_sold) as total_tickets,
            SUM(revenue) as total_revenue,
            MIN(timestamp) as earliest_sale,
            MAX(timestamp) as latest_sale
        FROM fan_staging.ticket_sales_stream
        """

        cursor = self.sf_conn.cursor()
        cursor.execute(summary_sql)
        result = cursor.fetchone()
        cursor.close()

        print("\n" + "=" * 50)
        print("📊 Snowflake Data Summary:")
        print(f"Total records: {result[0]:,}")
        print(f"Unique shows: {result[1]}")
        print(f"Total tickets: {result[2]:,}")
        print(f"Total revenue: ${result[3]:,.2f}")
        print(f"Time range: {result[4]} to {result[5]}")

    def close(self):
        """Close connections"""
        self.pg_conn.close()
        self.sf_conn.close()


def main():
    """Main function"""

    # Postgres configuration
    postgres_config = {
        "host": "localhost",
        "port": 5432,
        "database": "postgres",  # Use default database
        "user": os.getenv("POSTGRES_USER_INGEST", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD_INGEST", "password"),
    }

    print("🔄 Starting Postgres to Snowflake transfer...")

    try:
        # Get Snowflake connection
        snowflake_conn = get_snowflake_connection()

        # Create transfer object
        transfer = PostgresToSnowflake(postgres_config, snowflake_conn)

        # Transfer data
        transfer.transfer_data()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if "transfer" in locals():
            transfer.close()


if __name__ == "__main__":
    main()
