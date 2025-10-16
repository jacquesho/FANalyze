#!/usr/bin/env python3
"""
Data Validation Script for FANalyze 2.0
Validates data integrity and provides comprehensive reporting
"""

import os
import sys
from pathlib import Path
import pandas as pd
import psycopg
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

# Load environment variables
load_dotenv()

console = Console()


def get_postgres_connection():
    """Get PostgreSQL connection for data validation."""
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


def validate_table_structure(table_name="staging.test_ingest"):
    """
    Validate table structure and schema.
    
    Args:
        table_name (str): Table name to validate
    
    Returns:
        dict: Validation results
    """
    try:
        conn = get_postgres_connection()
        if not conn:
            return {"success": False, "error": "Connection failed"}
        
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'staging' AND table_name = 'test_ingest'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "columns": columns,
            "column_count": len(columns)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def validate_data_integrity(table_name="staging.test_ingest"):
    """
    Validate data integrity and quality.
    
    Args:
        table_name (str): Table name to validate
    
    Returns:
        dict: Validation results
    """
    try:
        conn = get_postgres_connection()
        if not conn:
            return {"success": False, "error": "Connection failed"}
        
        cursor = conn.cursor()
        
        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_records = cursor.fetchone()[0]
        
        # Check for null values
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(id) as non_null_ids,
                COUNT(data_content) as non_null_data_content,
                COUNT(file_name) as non_null_file_names,
                COUNT(loaded_at) as non_null_loaded_at
            FROM {table_name}
        """)
        
        null_check = cursor.fetchone()
        
        # Get data quality metrics
        cursor.execute(f"""
            SELECT 
                MIN(id) as min_id,
                MAX(id) as max_id,
                MIN(loaded_at) as earliest_loaded,
                MAX(loaded_at) as latest_loaded,
                COUNT(DISTINCT file_name) as unique_file_names
            FROM {table_name}
        """)
        
        quality_metrics = cursor.fetchone()
        
        # Check for duplicates
        cursor.execute(f"""
            SELECT id, COUNT(*) as duplicate_count
            FROM {table_name}
            GROUP BY id
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "total_records": total_records,
            "null_check": {
                "total_records": null_check[0],
                "non_null_ids": null_check[1],
                "non_null_data_content": null_check[2],
                "non_null_file_names": null_check[3],
                "non_null_loaded_at": null_check[4]
            },
            "quality_metrics": {
                "min_id": quality_metrics[0],
                "max_id": quality_metrics[1],
                "earliest_loaded": quality_metrics[2],
                "latest_loaded": quality_metrics[3],
                "unique_file_names": quality_metrics[4]
            },
            "duplicates": duplicates
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_sample_data(table_name="staging.test_ingest", limit=10):
    """
    Get sample data for review.
    
    Args:
        table_name (str): Table name to query
        limit (int): Number of records to return
    
    Returns:
        list: Sample data records
    """
    try:
        conn = get_postgres_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, data_content, file_name, loaded_at
            FROM {table_name}
            ORDER BY id
            LIMIT {limit}
        """)
        
        sample_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return sample_data
        
    except Exception as e:
        console.print(f"❌ Failed to get sample data: {e}", style="red")
        return []


def display_validation_report(table_name="staging.test_ingest"):
    """
    Display comprehensive validation report.
    
    Args:
        table_name (str): Table name to validate
    """
    console.print(f"\n🔍 Data Validation Report for {table_name}", style="bold blue")
    console.print("=" * 60)
    
    # Validate table structure
    console.print("\n1️⃣ Table Structure Validation", style="blue")
    structure_result = validate_table_structure(table_name)
    
    if structure_result["success"]:
        console.print("✅ Table structure is valid", style="green")
        
        # Display table structure
        table = Table(title="Table Structure")
        table.add_column("Column", style="cyan")
        table.add_column("Data Type", style="magenta")
        table.add_column("Nullable", style="yellow")
        table.add_column("Default", style="green")
        
        for col in structure_result["columns"]:
            table.add_row(str(col[0]), str(col[1]), str(col[2]), str(col[3]) if col[3] else "None")
        
        console.print(table)
    else:
        console.print(f"❌ Table structure validation failed: {structure_result['error']}", style="red")
        return False
    
    # Validate data integrity
    console.print("\n2️⃣ Data Integrity Validation", style="blue")
    integrity_result = validate_data_integrity(table_name)
    
    if integrity_result["success"]:
        console.print("✅ Data integrity validation completed", style="green")
        
        # Display data quality metrics
        metrics = integrity_result["quality_metrics"]
        null_check = integrity_result["null_check"]
        
        quality_table = Table(title="Data Quality Metrics")
        quality_table.add_column("Metric", style="cyan")
        quality_table.add_column("Value", style="magenta")
        
        quality_table.add_row("Total Records", str(integrity_result["total_records"]))
        quality_table.add_row("Min ID", str(metrics["min_id"]))
        quality_table.add_row("Max ID", str(metrics["max_id"]))
        quality_table.add_row("Unique File Names", str(metrics["unique_file_names"]))
        quality_table.add_row("Earliest Loaded", str(metrics["earliest_loaded"]))
        quality_table.add_row("Latest Loaded", str(metrics["latest_loaded"]))
        
        console.print(quality_table)
        
        # Check for null values
        null_table = Table(title="Null Value Check")
        null_table.add_column("Field", style="cyan")
        null_table.add_column("Non-Null Count", style="magenta")
        null_table.add_column("Status", style="green")
        
        null_table.add_row("ID", str(null_check["non_null_ids"]), "✅" if null_check["non_null_ids"] == null_check["total_records"] else "❌")
        null_table.add_row("Data Content", str(null_check["non_null_data_content"]), "✅" if null_check["non_null_data_content"] == null_check["total_records"] else "❌")
        null_table.add_row("File Name", str(null_check["non_null_file_names"]), "✅" if null_check["non_null_file_names"] == null_check["total_records"] else "❌")
        null_table.add_row("Loaded At", str(null_check["non_null_loaded_at"]), "✅" if null_check["non_null_loaded_at"] == null_check["total_records"] else "❌")
        
        console.print(null_table)
        
        # Check for duplicates
        if integrity_result["duplicates"]:
            console.print("⚠️ Duplicate records found:", style="yellow")
            dup_table = Table(title="Duplicate Records")
            dup_table.add_column("ID", style="cyan")
            dup_table.add_column("Count", style="magenta")
            
            for dup in integrity_result["duplicates"]:
                dup_table.add_row(str(dup[0]), str(dup[1]))
            
            console.print(dup_table)
        else:
            console.print("✅ No duplicate records found", style="green")
    
    else:
        console.print(f"❌ Data integrity validation failed: {integrity_result['error']}", style="red")
        return False
    
    # Display sample data
    console.print("\n3️⃣ Sample Data Review", style="blue")
    sample_data = get_sample_data(table_name, 5)
    
    if sample_data:
        sample_table = Table(title="Sample Data")
        sample_table.add_column("ID", style="cyan")
        sample_table.add_column("Data Content", style="magenta")
        sample_table.add_column("File Name", style="green")
        sample_table.add_column("Loaded At", style="yellow")
        
        for row in sample_data:
            sample_table.add_row(str(row[0]), str(row[1]), str(row[2]), str(row[3]))
        
        console.print(sample_table)
    else:
        console.print("❌ No sample data available", style="red")
        return False
    
    return True


def main():
    """Main function to run data validation."""
    console.print("🔍 FANalyze 2.0 - Data Validation", style="bold blue")
    console.print("=" * 50)
    
    # Run validation
    if display_validation_report():
        console.print("\n✅ Data validation completed successfully!", style="green")
        console.print("\n📚 Validation Summary:")
        console.print("   • Table structure validated")
        console.print("   • Data integrity checked")
        console.print("   • Sample data reviewed")
        console.print("   • Quality metrics calculated")
        
        return True
    else:
        console.print("\n❌ Data validation failed", style="red")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
