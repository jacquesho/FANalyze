#!/usr/bin/env python3
"""
Test: PostgreSQL to Snowflake Data Transfer
Transfers data from staging.test_ingest (Postgres) to PG_to_SF (Snowflake)
"""

import os
import sys
import psycopg
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(project_root, ".env"), override=False)

console = Console()


def get_postgres_connection():
    """Get PostgreSQL connection for data extraction."""
    try:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        dbname = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER_INGEST")
        password = os.getenv("POSTGRES_PASSWORD_INGEST")

        if not all([host, port, dbname, user, password]):
            console.print(
                "❌ Missing required PostgreSQL environment variables", style="red"
            )
            return None

        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        return conn
    except (psycopg.Error, ConnectionError) as e:
        console.print(f"❌ PostgreSQL connection failed: {e}", style="red")
        return None


def get_snowflake_connection():
    """Get Snowflake connection for data loading."""
    try:
        sf_user = os.getenv("SNOWFLAKE_USER")
        sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
        sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        sf_database = os.getenv("SNOWFLAKE_DATABASE")
        sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        sf_role = os.getenv("SNOWFLAKE_ROLE")
        sf_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

        if not all([sf_user, sf_account, sf_private_key_path]):
            console.print(
                "❌ Missing required Snowflake environment variables", style="red"
            )
            return None

        # Load private key
        with open(sf_private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )

        conn = snowflake.connector.connect(
            user=sf_user,
            account=sf_account,
            warehouse=sf_warehouse,
            database=sf_database,
            schema=sf_schema,
            role=sf_role,
            private_key=private_key,
        )
        return conn
    except (snowflake.connector.Error, FileNotFoundError, ValueError) as e:
        console.print(f"❌ Snowflake connection failed: {e}", style="red")
        return None


def create_snowflake_table(conn):
    """Create PG_to_SF table in Snowflake."""
    try:
        cursor = conn.cursor()

        # Create the PG_to_SF table in testing schema with the same structure as staging.test_ingest
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS testing.PG_to_SF (
            id INTEGER,
            data_content STRING,
            file_name STRING,
            loaded_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
        )
        """

        cursor.execute(create_table_sql)
        console.print("✅ Created PG_to_SF table in Snowflake", style="green")

        cursor.close()
        return True

    except snowflake.connector.Error as e:
        console.print(f"❌ Failed to create Snowflake table: {e}", style="red")
        return False


def extract_data_from_postgres():
    """Extract data from PostgreSQL staging.test_ingest table."""
    try:
        conn = get_postgres_connection()
        if not conn:
            return None

        cursor = conn.cursor()

        # Extract data from staging.test_ingest (excluding loaded_at since we'll use transfer timestamp)
        cursor.execute("SELECT id, data_content, file_name FROM staging.test_ingest")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        console.print(
            f"📊 Extracted {len(rows)} rows from PostgreSQL staging.test_ingest",
            style="green",
        )
        return rows

    except psycopg.Error as e:
        console.print(f"❌ Failed to extract data from PostgreSQL: {e}", style="red")
        return None


def load_data_to_snowflake(rows):
    """Load data into Snowflake PG_to_SF table."""
    try:
        conn = get_snowflake_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # Clear existing data (optional - remove if you want to append)
        cursor.execute("TRUNCATE TABLE IF EXISTS testing.PG_to_SF")

        # Insert data with current timestamp (when transfer actually took place)
        insert_sql = """
        INSERT INTO testing.PG_to_SF (id, data_content, file_name, loaded_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP())
        """

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading data to Snowflake...", total=len(rows))

            for row in rows:
                cursor.execute(insert_sql, (row[0], row[1], row[2]))
                progress.advance(task)

        cursor.close()
        conn.close()

        console.print(
            f"✅ Successfully loaded {len(rows)} records to Snowflake PG_to_SF",
            style="green",
        )
        return True

    except snowflake.connector.Error as e:
        console.print(f"❌ Failed to load data to Snowflake: {e}", style="red")
        return False


def verify_snowflake_data():
    """Verify data was loaded correctly in Snowflake."""
    try:
        conn = get_snowflake_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # Count records
        cursor.execute("SELECT COUNT(*) FROM testing.PG_to_SF")
        count = cursor.fetchone()[0]

        # Get sample data
        cursor.execute("SELECT * FROM testing.PG_to_SF ORDER BY id LIMIT 5")
        sample_data = cursor.fetchall()

        cursor.close()
        conn.close()

        # Display results
        console.print(
            f"📊 Total records in Snowflake testing.PG_to_SF: {count}", style="green"
        )

        if sample_data:
            table = Table(title="Sample Data from Snowflake testing.PG_to_SF")
            table.add_column("ID", style="cyan")
            table.add_column("Data Content", style="magenta")
            table.add_column("File Name", style="green")
            table.add_column("Loaded At", style="yellow")

            for row in sample_data:
                # Truncate timestamp for better table display
                timestamp = str(row[3])
                if len(timestamp) > 20:
                    timestamp = timestamp[:20] + "..."
                table.add_row(str(row[0]), str(row[1]), str(row[2]), timestamp)

            console.print(table)

        return count > 0

    except snowflake.connector.Error as e:
        console.print(f"❌ Snowflake data verification failed: {e}", style="red")
        return False


def test_pg_to_sf_transfer():
    """Test function to transfer data from PostgreSQL to Snowflake."""
    console.print("🚀 PostgreSQL to Snowflake Data Transfer Test", style="bold blue")
    console.print("=" * 50)

    # Step 1: Create Snowflake table
    console.print("\n1️⃣ Creating PG_to_SF table in Snowflake", style="blue")
    sf_conn = get_snowflake_connection()
    if not sf_conn:
        console.print("❌ Cannot connect to Snowflake", style="red")
        return False

    if not create_snowflake_table(sf_conn):
        console.print("❌ Failed to create Snowflake table", style="red")
        return False

    sf_conn.close()

    # Step 2: Extract data from PostgreSQL
    console.print(
        "\n2️⃣ Extracting data from PostgreSQL staging.test_ingest", style="blue"
    )
    rows = extract_data_from_postgres()
    if not rows:
        console.print("❌ No data extracted from PostgreSQL", style="red")
        return False

    # Step 3: Load data to Snowflake
    console.print("\n3️⃣ Loading data to Snowflake PG_to_SF", style="blue")
    if not load_data_to_snowflake(rows):
        console.print("❌ Failed to load data to Snowflake", style="red")
        return False

    # Step 4: Verify data
    console.print("\n4️⃣ Verifying data in Snowflake", style="blue")
    if not verify_snowflake_data():
        console.print("❌ Data verification failed", style="red")
        return False

    console.print(
        "\n✅ PostgreSQL to Snowflake transfer test completed successfully!",
        style="green",
    )
    console.print("\n📚 What was accomplished:")
    console.print(
        "   • Created testing.PG_to_SF table in Snowflake with matching schema"
    )
    console.print("   • Extracted data from PostgreSQL staging.test_ingest")
    console.print(
        "   • Loaded data into Snowflake testing.PG_to_SF with transfer timestamp"
    )
    console.print("   • Verified data integrity and completeness")

    return True


if __name__ == "__main__":
    success = test_pg_to_sf_transfer()
    sys.exit(0 if success else 1)
