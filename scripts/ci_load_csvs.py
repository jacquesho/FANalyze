#!/usr/bin/env python3
"""
CI-specific CSV loader for Snowflake
Loads CSV files from data/raw/csv/ into FAN_CI_RAW schema
"""

import os
import sys
import re
import pandas as pd
from datetime import datetime, timezone, timedelta
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
        database="FANALYZE_CI",  # CI database
        schema="FAN_RAW",  # Standard schema name
        role=os.getenv("SNOWFLAKE_ROLE"),
        private_key=private_key_der,
        authenticator="snowflake",
    )
    return conn


def create_schema_if_not_exists(conn):
    """Create FAN_RAW schema if it doesn't exist"""
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS FAN_RAW")
        print("✅ Schema FAN_RAW created or already exists")
    except Exception as e:
        print(f"❌ Error creating schema FAN_RAW: {e}")
        raise
    finally:
        cursor.close()


def create_table_if_not_exists(conn, table_name, df):
    """Create table if it doesn't exist based on DataFrame schema"""
    cursor = conn.cursor()

    # Special handling for raw_tickets table (matches streaming table structure)
    if table_name.upper() == "RAW_TICKETS":
        create_sql = """
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
        )
        """
        try:
            cursor.execute(create_sql)
            print(
                f"✅ Table FAN_RAW.{table_name} created or already exists (special structure)"
            )
        except Exception as e:
            print(f"❌ Error creating table FAN_RAW.{table_name}: {e}")
            raise
        finally:
            cursor.close()
        return

    # Generate CREATE TABLE statement based on DataFrame schema for other tables
    columns = []
    has_ingested_at = False
    for col, dtype in df.dtypes.items():
        col_upper = col.upper()
        col_lower = col.lower()
        if col_upper == "INGESTED_AT":
            has_ingested_at = True

        if dtype == "object":
            # Check for timestamp columns (updated, created, timestamp, _at suffix)
            if (
                "updated" in col_lower
                or "created" in col_lower
                or "timestamp" in col_lower
                or col_lower.endswith("_at")
                or col_lower == "collected_at"
            ):
                columns.append(f'"{col_upper}" TIMESTAMP_NTZ')
            elif "date" in col_lower and "str" not in col_lower:
                columns.append(f'"{col_upper}" DATE')
            else:
                columns.append(f'"{col_upper}" VARCHAR(16777216)')
        elif dtype == "int64":
            columns.append(f'"{col_upper}" NUMBER(19,0)')
        elif dtype == "float64":
            columns.append(f'"{col_upper}" FLOAT')
        else:
            columns.append(f'"{col_upper}" VARCHAR(16777216)')

    # Add INGESTED_AT column only if it doesn't exist
    if not has_ingested_at:
        columns.append('"INGESTED_AT" TIMESTAMP_NTZ')

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS FAN_RAW.{table_name} (
        {", ".join(columns)}
    )
    """

    try:
        cursor.execute(create_sql)
        print(f"✅ Table FAN_RAW.{table_name} created or already exists")
    except Exception as e:
        print(f"❌ Error creating table FAN_RAW.{table_name}: {e}")
        raise
    finally:
        cursor.close()


def load_csv_to_snowflake(csv_path, table_name):
    """Load CSV file into Snowflake table"""
    print(f"📂 Reading CSV: {csv_path}")

    # Read CSV
    try:
        df = pd.read_csv(csv_path)
        # Replace empty strings and whitespace-only strings with NaN to ensure proper NULL handling
        df = df.replace("", pd.NA)
        df = df.replace(r"^\s+$", pd.NA, regex=True)  # Replace whitespace-only strings
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

        # Add ingested_at timestamp only if column doesn't exist
        # Note: raw_tickets table uses synced_at (with DEFAULT), not ingested_at
        is_raw_tickets = table_name.upper() == "RAW_TICKETS"
        if not is_raw_tickets and "INGESTED_AT" not in df.columns:
            df["INGESTED_AT"] = datetime.now()

        # Drop and recreate table to ensure correct schema
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS FAN_RAW.{table_name}")
        print(f"🔄 Dropped existing table FAN_RAW.{table_name} (if existed)")

        # Recreate table with correct schema
        create_table_if_not_exists(conn, table_name, df)

        # Insert data
        print(f"📤 Inserting {len(df)} rows into FAN_RAW.{table_name}")

        # Convert DataFrame to list of tuples, handling NaN values
        data_to_insert = []
        is_raw_tickets = table_name.upper() == "RAW_TICKETS"

        for _, row in df.iterrows():
            row_data = []
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    row_data.append(None)
                else:
                    col_lower = col.lower()
                    col_upper = col.upper()

                    # Special handling for raw_tickets table
                    if is_raw_tickets:
                        if col_upper == "ID" or col_upper in [
                            "TICKETS_SOLD",
                            "CUMULATIVE_TICKETS_SOLD",
                            "VENUE_CAPACITY",
                            "DAYS_UNTIL_SHOW",
                        ]:
                            # INTEGER columns
                            try:
                                row_data.append(int(val))
                            except (ValueError, TypeError):
                                row_data.append(None)
                        elif col_upper in [
                            "REVENUE",
                            "CUMULATIVE_REVENUE",
                            "SALES_RATE",
                            "AVERAGE_TICKET_PRICE",
                        ]:
                            # DECIMAL columns
                            try:
                                row_data.append(float(val))
                            except (ValueError, TypeError):
                                row_data.append(None)
                        elif col_upper == "SHOW_DATE":
                            # DATE column
                            try:
                                if isinstance(val, (datetime, pd.Timestamp)):
                                    dt = pd.to_datetime(val)
                                else:
                                    dt = pd.to_datetime(
                                        str(val), dayfirst=True, errors="coerce"
                                    )
                                    if pd.isna(dt):
                                        dt = pd.to_datetime(str(val), errors="coerce")
                                if not pd.isna(dt):
                                    row_data.append(dt.strftime("%Y-%m-%d"))
                                else:
                                    row_data.append(None)
                            except Exception:
                                row_data.append(None)
                        elif col_upper in ["TIMESTAMP", "CREATED_AT"]:
                            # TIMESTAMP_TZ columns - keep timezone info
                            try:
                                if isinstance(val, (datetime, pd.Timestamp)):
                                    dt = pd.to_datetime(val)
                                else:
                                    dt = pd.to_datetime(str(val), errors="coerce")
                                if not pd.isna(dt):
                                    # Ensure timezone info (assume UTC if missing)
                                    if dt.tzinfo is None:
                                        dt = dt.tz_localize(timezone.utc)
                                    # Format as TIMESTAMP_TZ: YYYY-MM-DD HH:MI:SS+TZ:00
                                    # Snowflake accepts ISO format with timezone
                                    iso_str = dt.isoformat()
                                    # Convert to Snowflake format: YYYY-MM-DD HH:MI:SS+TZ:00
                                    if "+" in iso_str or iso_str.endswith("Z"):
                                        # Already has timezone
                                        row_data.append(
                                            iso_str.replace("T", " ").replace(
                                                "Z", "+00:00"
                                            )
                                        )
                                    else:
                                        # Add UTC timezone
                                        row_data.append(
                                            iso_str.replace("T", " ") + "+00:00"
                                        )
                                else:
                                    row_data.append(None)
                            except Exception:
                                # Fallback: try to parse as string
                                val_str = str(val)
                                row_data.append(val_str)
                        else:
                            # VARCHAR columns
                            row_data.append(str(val))
                    # Convert date strings to Snowflake-compatible format (YYYY-MM-DD)
                    elif "date" in col_lower and "str" not in col_lower:
                        val_str = str(val)
                        try:
                            # Try parsing with pandas (handles various formats including DD-MM-YYYY)
                            if isinstance(val, (datetime, pd.Timestamp)):
                                dt = pd.to_datetime(val)
                            else:
                                # Try parsing with dayfirst=True for DD-MM-YYYY format
                                dt = pd.to_datetime(
                                    val_str, dayfirst=True, errors="coerce"
                                )
                                if pd.isna(dt):
                                    # Fallback to standard parsing
                                    dt = pd.to_datetime(val_str, errors="coerce")

                            if not pd.isna(dt):
                                # Format as DATE: YYYY-MM-DD
                                val_str = dt.strftime("%Y-%m-%d")
                            else:
                                # If parsing fails, keep original string
                                val_str = str(val)
                        except Exception:
                            # Fallback: keep original string if parsing fails
                            val_str = str(val)

                        row_data.append(val_str)
                    # Convert timestamp strings to Snowflake-compatible format
                    elif (
                        "updated" in col_lower
                        or "created" in col_lower
                        or "timestamp" in col_lower
                        or col_lower.endswith("_at")
                        or col_lower == "collected_at"
                    ):
                        # Convert ISO timestamp to Bangkok/HCMC time (ICT, UTC+7)
                        val_str = str(val)
                        try:
                            # Parse the timestamp using pandas (handles various formats)
                            if isinstance(val, (datetime, pd.Timestamp)):
                                dt = pd.to_datetime(val)
                            else:
                                # Parse string timestamp - pandas handles ISO with timezone
                                dt = pd.to_datetime(val_str)

                            # Ensure we have timezone info (assume UTC if missing)
                            if dt.tzinfo is None:
                                dt = dt.tz_localize(timezone.utc)

                            # Convert to UTC first
                            dt_utc = dt.tz_convert(timezone.utc)

                            # Convert UTC to Bangkok/HCMC time (ICT = UTC+7)
                            ict_offset = timedelta(hours=7)
                            dt_ict = dt_utc.to_pydatetime() + ict_offset

                            # Format as TIMESTAMP_NTZ (no timezone): YYYY-MM-DD HH:MI:SS.fff
                            val_str = (
                                dt_ict.strftime("%Y-%m-%d %H:%M:%S.%f")
                                .rstrip("0")
                                .rstrip(".")
                            )
                        except Exception:
                            # Fallback: just remove timezone if parsing fails
                            if "T" in val_str:
                                val_str = val_str.replace("T", " ")
                                val_str = re.sub(r"[+-]\d{4}$", "", val_str).strip()

                        row_data.append(val_str)
                    else:
                        row_data.append(str(val))
            data_to_insert.append(tuple(row_data))

        # Build INSERT statement
        # Note: raw_tickets table doesn't have INGESTED_AT (uses synced_at with DEFAULT)
        # Exclude INGESTED_AT from INSERT for raw_tickets table
        if is_raw_tickets:
            insert_columns = [col for col in df.columns if col.upper() != "INGESTED_AT"]
        else:
            insert_columns = df.columns
        
        columns_upper = [f'"{col.upper()}"' for col in insert_columns]
        placeholders = ", ".join(["%s"] * len(insert_columns))
        insert_sql = (
            f"INSERT INTO FAN_RAW.{table_name} ({', '.join(columns_upper)}) "
            f"VALUES ({placeholders})"
        )
        
        # Filter data_to_insert to match insert_columns (exclude INGESTED_AT for raw_tickets)
        if is_raw_tickets:
            ingested_at_idx = None
            for i, col in enumerate(df.columns):
                if col.upper() == "INGESTED_AT":
                    ingested_at_idx = i
                    break
            if ingested_at_idx is not None:
                filtered_data = []
                for row_tuple in data_to_insert:
                    filtered_data.append(
                        tuple(val for i, val in enumerate(row_tuple) if i != ingested_at_idx)
                    )
                data_to_insert = filtered_data

        # Insert in batches
        cursor.executemany(insert_sql, data_to_insert)
        conn.commit()

        print(f"✅ Successfully loaded {len(df)} rows into FAN_RAW.{table_name}")
        cursor.close()
        return True

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main function to load CSV files"""
    print("🚀 CI CSV Loader - Loading data into FANALYZE_CI.FAN_RAW schema")
    print("=" * 60)

    # CSV file mappings
    csv_files = {
        "shows_history.csv": "SHOWS_HIS",
        "shows_future.csv": "SHOWS_FUTURE",
        "tickets_sample.csv": "raw_tickets",
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
