#!/usr/bin/env python3
"""
CSV Ingestion Script for FANalyze Project
Ingests CSV files directly into Snowflake tables without staging
"""

import os
import sys
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from datetime import datetime
import logging

# Add the config directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from api_config import get_snowflake_connection
except ImportError:
    print("Error: Could not import Snowflake configuration")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_table_if_not_exists(conn, table_name, df):
    """Create table if it doesn't exist based on DataFrame schema"""
    cursor = conn.cursor()
    
    # Generate CREATE TABLE statement based on DataFrame
    columns = []
    for col, dtype in df.dtypes.items():
        if dtype == 'object':
            # Check if it's a date column
            if 'date' in col.lower():
                columns.append(f'"{col}" DATE')
            else:
                columns.append(f'"{col}" VARCHAR(16777216)')
        elif dtype == 'int64':
            columns.append(f'"{col}" NUMBER(19,0)')
        elif dtype == 'float64':
            columns.append(f'"{col}" FLOAT')
        else:
            columns.append(f'"{col}" VARCHAR(16777216)')
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {', '.join(columns)},
        INGESTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
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

def ingest_csv_to_snowflake(csv_file_path, table_name, schema='FAN_RAW'):
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
        df['INGESTED_AT'] = datetime.now()
        
        # Write data to Snowflake
        logger.info(f"Writing {len(df)} rows to {full_table_name}")
        success, nchunks, nrows, _ = write_pandas(
            conn, 
            df, 
            table_name=table_name,
            schema=schema,
            auto_create_table=False,
            overwrite=True  # Replace existing data
        )
        
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
    csv_files = {
        'all_shows_2015_to_2025_with_tickets.csv': 'SHOWS_HIS',
        'real_us_future_concerts_current_sales_2025_2026.csv': 'SHOWS_FUTURE'
    }
    
    base_path = os.path.dirname(os.path.dirname(__file__))  # Go up to FANalyze_v2.0
    
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
    
    logger.info(f"📊 Ingestion Summary: {success_count}/{total_count} files processed successfully")
    
    if success_count == total_count:
        logger.info("🎉 All CSV files ingested successfully!")
        return True
    else:
        logger.error("⚠️  Some files failed to ingest")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
