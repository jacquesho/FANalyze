#!/usr/bin/env python3
"""
CSV Data Loader for FANalyze 2.0
Loads CSV data into PostgreSQL staging.test_ingest table
"""

import os
import sys
from pathlib import Path
import json
import pandas as pd
import psycopg
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
load_dotenv()

console = Console()


def get_postgres_connection():
    """Get PostgreSQL connection for data loading."""
    try:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        dbname = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER_INGEST")
        password = os.getenv("POSTGRES_PASSWORD_INGEST")

        missing = [name for name, val in [
            ("POSTGRES_HOST", host),
            ("POSTGRES_PORT", port),
            ("POSTGRES_DB", dbname),
            ("POSTGRES_USER_INGEST", user),
            ("POSTGRES_PASSWORD_INGEST", password),
        ] if not val]

        if missing:
            console.print("❌ Missing required environment variables: " + ", ".join(missing), style="red")
            return None

        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        return conn
    except Exception as e:
        console.print(f"❌ PostgreSQL connection failed: {e}", style="red")
        return None


def load_csv_to_postgres(csv_file_path, table_name="staging.test_ingest"):
    """
    Load CSV data into PostgreSQL staging table.
    
    Args:
        csv_file_path (str): Path to the CSV file
        table_name (str): Target table name (default: staging.test_ingest)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read CSV file
        console.print(f"📁 Reading CSV file: {csv_file_path}", style="blue")
        df = pd.read_csv(csv_file_path)
        
        console.print(f"📊 CSV contains {len(df)} rows and {len(df.columns)} columns", style="green")
        console.print(f"📋 Columns: {list(df.columns)}", style="cyan")
        
        # Get PostgreSQL connection
        conn = get_postgres_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Prepare data for insertion
        rows = []
        for _, row in df.iterrows():
            rows.append((
                int(row['id']),
                str(row['data_content']),
                str(row['file_name'])
            ))
        
        # Insert data with local timezone
        insert_sql = f"""
        INSERT INTO {table_name} (id, data_content, file_name, loaded_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (id) DO UPDATE SET
            data_content = EXCLUDED.data_content,
            file_name = EXCLUDED.file_name,
            loaded_at = NOW()
        """
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading data to PostgreSQL...", total=len(rows))
            
            cursor.executemany(insert_sql, rows)
            conn.commit()
            
            progress.update(task, completed=len(rows))
        
        cursor.close()
        conn.close()
        
        console.print(f"✅ Successfully loaded {len(rows)} records to {table_name}", style="green")
        return True
        
    except Exception as e:
        console.print(f"❌ CSV loading failed: {e}", style="red")
        return False


def verify_data_loaded(table_name="staging.test_ingest"):
    """
    Verify that data was loaded correctly.
    
    Args:
        table_name (str): Table name to verify
    
    Returns:
        bool: True if data exists, False otherwise
    """
    try:
        conn = get_postgres_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Count records
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id LIMIT 5")
        sample_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Display results
        console.print(f"📊 Total records in {table_name}: {count}", style="green")
        
        if sample_data:
            table = Table(title=f"Sample Data from {table_name}")
            table.add_column("ID", style="cyan")
            table.add_column("Data Content", style="magenta")
            table.add_column("File Name", style="green")
            table.add_column("Loaded At", style="yellow")
            
            for row in sample_data:
                table.add_row(str(row[0]), str(row[1]), str(row[2]), str(row[3]))
            
            console.print(table)
        
        return count > 0
        
    except Exception as e:
        console.print(f"❌ Data verification failed: {e}", style="red")
        return False


def load_jsonl_to_postgres(jsonl_file_path, table_name="staging.test_ingest"):
    """
    Load JSONL data into PostgreSQL staging table.
    Each line should represent a TicketSaleRecord dict with keys id, data_content, file_name.
    If a line only contains the payload, we will wrap it into the schema.
    """
    try:
        console.print(f"📁 Reading JSONL file: {jsonl_file_path}", style="blue")

        conn = get_postgres_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        insert_sql = f"""
        INSERT INTO {table_name} (id, data_content, file_name, loaded_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (id) DO UPDATE SET
            data_content = EXCLUDED.data_content,
            file_name = EXCLUDED.file_name,
            loaded_at = NOW()
        """

        total = 0
        with open(jsonl_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                # Accept both {id,data_content,file_name} and raw payload forms
                if all(k in obj for k in ("id", "data_content", "file_name")):
                    row = (int(obj["id"]), str(obj["data_content"]), str(obj["file_name"]))
                else:
                    # Wrap raw payload
                    total += 1
                    row = (total, json.dumps(obj, separators=(",", ":")), Path(jsonl_file_path).name)
                cursor.execute(insert_sql, row)
                total += 1
                console.print(f"⬆️ inserted row {total}", style="cyan")

        conn.commit()
        cursor.close()
        conn.close()
        console.print(f"✅ Successfully loaded {total} JSONL records to {table_name}", style="green")
        return True
    except Exception as e:
        console.print(f"❌ JSONL loading failed: {e}", style="red")
        return False


def main():
    """Main function to load CSV or JSONL data into PostgreSQL."""
    console.print("🚀 FANalyze 2.0 - CSV Data Loader", style="bold blue")
    console.print("=" * 50)
    
    # Get CSV file path (use absolute path to avoid working directory issues)
    # Allow override via environment variable CSV_FILE_PATH
    override_path = os.getenv("CSV_FILE_PATH")
    if override_path:
        csv_file_path = Path(override_path)
    else:
        script_dir = Path(__file__).parent.parent.parent
        csv_file_path = script_dir / "tests" / "DB_tests" / "sample_data.csv"
    
    console.print(f"🔍 Looking for CSV file at: {csv_file_path}", style="cyan")
    console.print(f"🔍 Current working directory: {os.getcwd()}", style="cyan")
    
    if not os.path.exists(csv_file_path):
        console.print(f"❌ CSV file not found: {csv_file_path}", style="red")
        return False
    
    # Load CSV data
    console.print(f"\n1️⃣ Loading data from {csv_file_path}", style="blue")
    ext = csv_file_path.suffix.lower()
    if ext == ".jsonl":
        if not load_jsonl_to_postgres(csv_file_path):
            console.print("❌ JSONL loading failed", style="red")
            return False
    else:
        if not load_csv_to_postgres(csv_file_path):
            console.print("❌ CSV loading failed", style="red")
            return False
    
    # Verify data
    console.print(f"\n2️⃣ Verifying data in staging.test_ingest", style="blue")
    if not verify_data_loaded():
        console.print("❌ Data verification failed", style="red")
        return False
    
    console.print("\n✅ CSV data loading completed successfully!", style="green")
    console.print("\n📚 What was accomplished:")
    console.print("   • CSV data loaded into PostgreSQL staging.test_ingest table")
    console.print("   • Data validation and verification completed")
    console.print("   • Foundation ready for further data processing")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
