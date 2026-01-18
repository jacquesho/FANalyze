#!/usr/bin/env python3
"""
CSV Ingestion Script for FANalyze Project
Ingests CSV files directly into Snowflake tables without staging
"""

import os
import sys
import pandas as pd
from datetime import datetime
import logging

# Add the config directory to the path
# Try project_config first (when running in Airflow), then fall back to ../config (local development)
config_paths = [
    "/opt/airflow/project_config",  # Mounted in Airflow container
    os.path.join(os.path.dirname(__file__), "..", "config"),  # Local development
]
for config_path in config_paths:
    if os.path.exists(config_path):
        sys.path.insert(0, config_path)
        break

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


def create_table_if_not_exists(conn, table_name, df):
    """Create table if it doesn't exist based on DataFrame schema"""
    cursor = conn.cursor()

    # Generate CREATE TABLE statement based on DataFrame
    columns = []
    for col, dtype in df.dtypes.items():
        if dtype == "object":
            # Check if it's a date column
            if "date" in col.lower():
                columns.append(f'"{col}" DATE')
            else:
                columns.append(f'"{col}" VARCHAR(16777216)')
        elif dtype == "int64":
            columns.append(f'"{col}" NUMBER(19,0)')
        elif dtype == "float64":
            columns.append(f'"{col}" FLOAT')
        else:
            columns.append(f'"{col}" VARCHAR(16777216)')

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {", ".join(columns)}
    )
    """

    try:
        cursor.execute(create_sql)
        logger.info(f"Table {table_name} created or already exists")
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {e}")
        raise
    finally:
        cursor.close()


def ingest_csv_to_snowflake(csv_file_path, table_name, schema="FAN_RAW"):
    """Ingest CSV file directly into Snowflake table"""

    # Read CSV file
    logger.info(f"Reading CSV file: {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path)
        logger.info(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Error reading CSV file {csv_file_path}: {e}")
        return False

    # Connect to Snowflake
    try:
        conn = get_snowflake_connection()
        logger.info("Connected to Snowflake successfully")
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {e}")
        return False

    try:
        # Create table if it doesn't exist
        full_table_name = f"{schema}.{table_name}"
        create_table_if_not_exists(conn, full_table_name, df)

        # Add ingested_at timestamp
        df["INGESTED_AT"] = datetime.now()

        # Write data to Snowflake using simple INSERT statements
        logger.info(f"Writing {len(df)} rows to {full_table_name}")

        cursor = conn.cursor()

        # Clear existing data
        cursor.execute(f"DELETE FROM {full_table_name}")

        # Map CSV columns to table columns
        if table_name == "SHOWS_HIS":
            # Historical shows mapping
            column_mapping = {
                "ARTIST_ID": "ARTIST_ID",
                "ARTIST_NAME": "ARTIST_NAME",
                "SHOW_ID": "SHOW_ID",
                "SHOW_DATE": "SHOW_DATE",
                "SOURCE": "SOURCE",
                "VENUE_NAME": "VENUE_NAME",
                "VENUE_ID": "VENUE_ID",
                "VENUE_TYPE": "VENUE_TYPE",
                "VENUE_CAPACITY": "VENUE_CAPACITY",
                "CITY_NAME": "CITY_NAME",
                "STATE_CODE": "STATE_CODE",
                "COUNTRY_NAME": "COUNTRY_NAME",
                "MARKET_SIZE": "MARKET_SIZE",
                "ARTIST_TIER": "ARTIST_TIER",
                "TICKETS_SOLD": "TICKETS_SOLD",
                "SELLOUT_STATUS": "SELLOUT_STATUS",
                "ATTENDANCE_RATE": "ATTENDANCE_RATE",
                "AVERAGE_TICKET_PRICE": "AVERAGE_TICKET_PRICE",
                "TICKET_PRICE_RANGE": "TICKET_PRICE_RANGE",
                "REVENUE": "REVENUE",
                "EVENT_DATE_STR": "EVENT_DATE_STR",
                "LAST_UPDATED": "LAST_UPDATED",
                "INGESTED_AT": "INGESTED_AT",
            }
        else:
            # Future shows mapping
            column_mapping = {
                "artist_name": "ARTIST_NAME",
                "show_date": "SHOW_DATE",
                "venue_name": "VENUE_NAME",
                "city_name": "CITY_NAME",
                "state_code": "STATE_CODE",
                "country_name": "COUNTRY_NAME",
                "source": "SOURCE",
                "collected_at": "COLLECTED_AT",
                "show_id": "SHOW_ID",
                "venue_id": "VENUE_ID",
                "TICKETS_SOLD_SO_FAR": "TICKETS_SOLD",
                "AVERAGE_TICKET_PRICE": "AVERAGE_TICKET_PRICE",
                "CURRENT_REVENUE": "REVENUE",
                "INGESTED_AT": "INGESTED_AT",
            }

        # Get columns that exist in both CSV and table
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        column_names = ", ".join(
            [f'"{column_mapping[col]}"' for col in available_columns]
        )
        placeholders = ", ".join(["%s"] * len(available_columns))

        # Prepare data for insertion using mapped columns
        data_to_insert = []
        for _, row in df.iterrows():
            row_data = []
            for col in available_columns:
                val = row[col]
                if pd.isna(val):
                    row_data.append(None)
                else:
                    row_data.append(str(val))
            data_to_insert.append(tuple(row_data))

        # Insert data in batches
        insert_sql = (
            f"INSERT INTO {full_table_name} ({column_names}) VALUES ({placeholders})"
        )

        try:
            cursor.executemany(insert_sql, data_to_insert)
            conn.commit()
            success = True
            nrows = len(df)
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            success = False
            nrows = 0
        finally:
            cursor.close()

        if success:
            logger.info(f"Successfully ingested {nrows} rows into {full_table_name}")
            return True
        else:
            logger.error(f"Failed to ingest data into {full_table_name}")
            return False

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main function to ingest CSV files"""

    # Define file mappings
    csv_files = {"shows_history.csv": "SHOWS_HIS", "shows_future.csv": "SHOWS_FUTURE"}

    base_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "raw", "csv"
    )  # Go to data/raw/csv

    success_count = 0
    total_count = len(csv_files)

    for csv_file, table_name in csv_files.items():
        csv_path = os.path.join(base_path, csv_file)

        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found: {csv_path}")
            continue

        logger.info(f"Processing {csv_file} -> {table_name}")

        if ingest_csv_to_snowflake(csv_path, table_name):
            success_count += 1
            logger.info(f"✅ Successfully processed {csv_file}")
        else:
            logger.error(f"❌ Failed to process {csv_file}")

    logger.info(
        f"📊 Ingestion Summary: {success_count}/{total_count} files processed successfully"
    )

    if success_count == total_count:
        logger.info("🎉 All CSV files ingested successfully!")
        return True
    else:
        logger.error("⚠️  Some files failed to ingest")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
