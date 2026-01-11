#!/usr/bin/env python3
"""
CI-specific CSV loader for Snowflake
Loads CSV files from data/raw/csv/ into FAN_CI_RAW schema
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
import snowflake.connector
from cryptography.hazmat.primitives import serialization

# Get project root
project_root = Path(__file__).parent.parent
csv_dir = project_root / "data" / "raw" / "csv"


def get_snowflake_connection():
    """Get Snowflake connection using CI environment variables"""
    # Read private key from file
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH", ".secrets/rsa_key.p8")
    key_pwd = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD")

    if not os.path.exists(key_path):
        raise Exception(f"Private key file not found: {key_path}")

    with open(key_path, "rb") as key_file:
        private_key_pem = key_file.read()

    # Load private key
    if key_pwd:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=key_pwd.encode() if isinstance(key_pwd, str) else key_pwd,
        )
    else:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
        )

    # Convert to DER format
    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="FAN_CI_RAW",  # CI-specific raw schema
        role=os.getenv("SNOWFLAKE_ROLE"),
        private_key=private_key_der,
        authenticator="snowflake",
    )
    return conn


def create_schema_if_not_exists(conn):
    """Create FAN_CI_RAW schema if it doesn't exist"""
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS FAN_CI_RAW")
        print("✅ Schema FAN_CI_RAW created or already exists")
    except Exception as e:
        print(f"❌ Error creating schema FAN_CI_RAW: {e}")
        raise
    finally:
        cursor.close()


def create_table_if_not_exists(conn, table_name, df):
    """Create table if it doesn't exist based on DataFrame schema"""
    cursor = conn.cursor()

    # Generate CREATE TABLE statement based on DataFrame
    columns = []
    for col, dtype in df.dtypes.items():
        col_upper = col.upper()
        if dtype == "object":
            if "date" in col.lower():
                columns.append(f'"{col_upper}" DATE')
            else:
                columns.append(f'"{col_upper}" VARCHAR(16777216)')
        elif dtype == "int64":
            columns.append(f'"{col_upper}" NUMBER(19,0)')
        elif dtype == "float64":
            columns.append(f'"{col_upper}" FLOAT')
        else:
            columns.append(f'"{col_upper}" VARCHAR(16777216)')

    # Add INGESTED_AT column
    columns.append('"INGESTED_AT" TIMESTAMP_NTZ')

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS FAN_CI_RAW.{table_name} (
        {", ".join(columns)}
    )
    """

    try:
        cursor.execute(create_sql)
        print(f"✅ Table FAN_CI_RAW.{table_name} created or already exists")
    except Exception as e:
        print(f"❌ Error creating table FAN_CI_RAW.{table_name}: {e}")
        raise
    finally:
        cursor.close()


def load_csv_to_snowflake(csv_path, table_name):
    """Load CSV file into Snowflake table"""
    print(f"📂 Reading CSV: {csv_path}")

    # Read CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False

    # Connect to Snowflake
    try:
        conn = get_snowflake_connection()
        print("✅ Connected to Snowflake")
    except Exception as e:
        print(f"❌ Error connecting to Snowflake: {e}")
        return False

    try:
        # Create schema if it doesn't exist
        create_schema_if_not_exists(conn)

        # Create table if it doesn't exist
        create_table_if_not_exists(conn, table_name, df)

        # Add ingested_at timestamp
        df["INGESTED_AT"] = datetime.now()

        # Clear existing data
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM FAN_CI_RAW.{table_name}")

        # Insert data
        print(f"📤 Inserting {len(df)} rows into FAN_CI_RAW.{table_name}")

        # Convert DataFrame to list of tuples, handling NaN values
        data_to_insert = []
        for _, row in df.iterrows():
            row_data = []
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    row_data.append(None)
                else:
                    row_data.append(str(val))
            data_to_insert.append(tuple(row_data))

        # Build INSERT statement
        columns_upper = [f'"{col.upper()}"' for col in df.columns]
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql = (
            f"INSERT INTO FAN_CI_RAW.{table_name} ({', '.join(columns_upper)}) "
            f"VALUES ({placeholders})"
        )

        # Insert in batches
        cursor.executemany(insert_sql, data_to_insert)
        conn.commit()

        print(f"✅ Successfully loaded {len(df)} rows into FAN_CI_RAW.{table_name}")
        cursor.close()
        return True

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main function to load CSV files"""
    print("🚀 CI CSV Loader - Loading data into FAN_CI_RAW schema")
    print("=" * 60)

    # CSV file mappings
    csv_files = {
        "shows_history.csv": "SHOWS_HIS",
        "shows_future.csv": "SHOWS_FUTURE"
    }

    success_count = 0
    total_count = len(csv_files)

    for csv_file, table_name in csv_files.items():
        csv_path = csv_dir / csv_file

        if not csv_path.exists():
            print(f"⚠️  CSV file not found: {csv_path}")
            continue

        print(f"\n📋 Processing {csv_file} -> {table_name}")

        if load_csv_to_snowflake(csv_path, table_name):
            success_count += 1
        else:
            print(f"❌ Failed to process {csv_file}")
            return False

    print(f"\n📊 Summary: {success_count}/{total_count} files loaded successfully")

    if success_count == total_count:
        print("🎉 All CSV files loaded successfully!")
        return True
    else:
        print("❌ Some files failed to load")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
