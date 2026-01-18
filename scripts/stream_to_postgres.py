#!/usr/bin/env python3
"""
Stream ticket sales data to Postgres database
Receives streaming data and writes to Postgres for later Snowflake ingestion
"""

import os
import sys
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent / "config"))


class PostgresTicketWriter:
    def __init__(self, db_config):
        """Initialize Postgres connection"""
        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        """Create the ticket_sales table if it doesn't exist"""

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS staging.ticket_sales (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_ticket_sales_show_id ON staging.ticket_sales(show_id);
        CREATE INDEX IF NOT EXISTS idx_ticket_sales_timestamp ON staging.ticket_sales(timestamp);
        CREATE INDEX IF NOT EXISTS idx_ticket_sales_show_date ON staging.ticket_sales(show_date);
        """

        self.cur.execute(create_table_sql)
        self.conn.commit()
        print("✅ Postgres database setup complete")

    def write_sale_event(self, sale_event):
        """Write a sale event to Postgres immediately (row-by-row ingestion)"""

        insert_sql = """
        INSERT INTO staging.ticket_sales (
            timestamp, show_id, artist_name, venue_name, show_date,
            city_name, state_code, tickets_sold, cumulative_tickets_sold,
            revenue, cumulative_revenue, venue_capacity, sales_rate,
            days_until_show, artist_tier, average_ticket_price
        ) VALUES (
            %(timestamp)s, %(show_id)s, %(artist_name)s, %(venue_name)s, %(show_date)s,
            %(city_name)s, %(state_code)s, %(tickets_sold)s, %(cumulative_tickets_sold)s,
            %(revenue)s, %(cumulative_revenue)s, %(venue_capacity)s, %(sales_rate)s,
            %(days_until_show)s, %(artist_tier)s, %(average_ticket_price)s
        )
        """

        try:
            # Convert timestamp string to datetime
            sale_event["timestamp"] = datetime.fromisoformat(
                sale_event["timestamp"].replace("Z", "+00:00")
            )
            sale_event["show_date"] = datetime.fromisoformat(
                sale_event["show_date"]
            ).date()

            # Execute and commit immediately (row-by-row)
            self.cur.execute(insert_sql, sale_event)
            self.conn.commit()

            # Return success for real-time feedback
            return True

        except Exception as e:
            # Rollback on error and re-raise
            self.conn.rollback()
            raise e

    def verify_row_ingestion(self, show_id, timestamp):
        """Verify that a specific row was successfully ingested"""

        verify_sql = """
        SELECT COUNT(*) FROM staging.ticket_sales 
        WHERE show_id = %s AND timestamp = %s
        """

        self.cur.execute(verify_sql, (show_id, timestamp))
        count = self.cur.fetchone()[0]
        return count > 0

    def get_stats(self):
        """Get current database statistics"""

        stats_sql = """
        SELECT 
            COUNT(*) as total_sales,
            COUNT(DISTINCT show_id) as unique_shows,
            SUM(tickets_sold) as total_tickets,
            SUM(revenue) as total_revenue,
            MIN(timestamp) as first_sale,
            MAX(timestamp) as last_sale
        FROM staging.ticket_sales
        """

        self.cur.execute(stats_sql)
        result = self.cur.fetchone()

        return {
            "total_sales": result[0],
            "unique_shows": result[1],
            "total_tickets": result[2],
            "total_revenue": result[3],
            "first_sale": result[4],
            "last_sale": result[5],
        }

    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()


def run_stream_to_postgres(duration_minutes=5, speed_multiplier=10):
    """Run the streaming ticket sales and write to Postgres"""

    # Postgres configuration
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "database": os.getenv("POSTGRES_DB", "postgres"),
        "user": os.getenv("POSTGRES_USER_INGEST", "user_fanalyze_ingest"),
        "password": os.getenv("POSTGRES_PASSWORD_INGEST", "fanalyze_ingest_password"),
    }

    print("🚀 Starting ticket sales stream to Postgres...")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Speed: {speed_multiplier}x")
    print("=" * 50)

    # Initialize Postgres writer
    writer = PostgresTicketWriter(db_config)

    try:
        # Start the streaming process
        process = subprocess.Popen(
            [
                sys.executable,
                "scripts/stream_tickets.py",
                "--speed",
                str(speed_multiplier),
                "--duration",
                str(duration_minutes),
                "--format",
                "jsonl",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd(),
        )

        # Read and process each line as it arrives (row-by-row ingestion)
        event_count = 0
        print("🔄 Starting real-time row-by-row ingestion...")

        for line in process.stdout:
            if line.strip():
                try:
                    # Parse JSON immediately as it arrives
                    sale_event = json.loads(line.strip())

                    # Write to Postgres immediately (row-by-row)
                    success = writer.write_sale_event(sale_event)

                    if success:
                        event_count += 1

                        # Verify the row was ingested (optional verification)
                        # verify_ingestion = writer.verify_row_ingestion(sale_event['show_id'], sale_event['timestamp'])

                        # Show progress for every event (real-time feedback)
                        print(
                            f"✅ Row {event_count}: {sale_event['artist_name']} - {sale_event['tickets_sold']} tickets (${sale_event['revenue']:,.2f})"
                        )
                    else:
                        print(f"❌ Failed to ingest row: {sale_event['artist_name']}")

                except json.JSONDecodeError:
                    print(f"⚠️ Skipping invalid JSON: {line.strip()[:100]}...")
                    continue
                except Exception as e:
                    print(f"❌ Error writing row to Postgres: {e}")

        print(f"📊 Total rows ingested: {event_count}")

        # Wait for process to complete
        process.wait()

        # Show final stats
        stats = writer.get_stats()
        print("\n" + "=" * 50)
        print("📊 Final Statistics:")
        print(f"Total sales events: {stats['total_sales'] or 0:,}")
        print(f"Unique shows: {stats['unique_shows'] or 0}")
        print(f"Total tickets sold: {stats['total_tickets'] or 0:,}")
        print(f"Total revenue: ${stats['total_revenue'] or 0:,.2f}")
        print(
            f"Time range: {stats['first_sale'] or 'N/A'} to {stats['last_sale'] or 'N/A'}"
        )

    except KeyboardInterrupt:
        print("\n⏹️ Stream stopped by user")
    finally:
        writer.close()


def main():
    """Main function"""

    parser = argparse.ArgumentParser(description="Stream ticket sales to Postgres")
    parser.add_argument(
        "--duration", type=int, default=5, help="Duration in minutes (default: 5)"
    )
    parser.add_argument(
        "--speed", type=float, default=10, help="Speed multiplier (default: 10)"
    )

    args = parser.parse_args()

    run_stream_to_postgres(duration_minutes=args.duration, speed_multiplier=args.speed)


if __name__ == "__main__":
    main()
