#!/usr/bin/env python3
"""
Main CSV Ingestion Script for FANalyze 2.0
Orchestrates the complete CSV data ingestion pipeline
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))

from database.csv_loader import main as load_csv
from validation.data_validation import main as validate_data

console = Console()


def initialize_database():
    """Initialize PostgreSQL database with required tables."""
    try:
        from database.csv_loader import get_postgres_connection
        
        conn = get_postgres_connection()
        if not conn:
            console.print("❌ Cannot connect to PostgreSQL", style="red")
            return False
        
        cursor = conn.cursor()
        
        # Read and execute SQL initialization script
        sql_file = Path(__file__).parent.parent / "sql" / "init_test_ingest.sql"
        
        if sql_file.exists():
            with open(sql_file, 'r') as f:
                sql_script = f.read()
            
            cursor.execute(sql_script)
            conn.commit()
            
            console.print("✅ Database initialized successfully", style="green")
        else:
            console.print(f"❌ SQL initialization file not found: {sql_file}", style="red")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        console.print(f"❌ Database initialization failed: {e}", style="red")
        return False


def run_csv_ingestion_pipeline():
    """Run the complete CSV ingestion pipeline."""
    console.print("🚀 FANalyze 2.0 - CSV Ingestion Pipeline", style="bold blue")
    console.print("=" * 60)
    
    # Step 1: Initialize database
    console.print("\n1️⃣ Initializing Database", style="blue")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up database...", total=None)
        
        if not initialize_database():
            console.print("❌ Database initialization failed", style="red")
            return False
        
        progress.update(task, completed=100)
    
    console.print("✅ Database initialized", style="green")
    
    # Step 2: Load CSV data
    console.print("\n2️⃣ Loading Data (CSV or JSONL)", style="blue")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
            task = progress.add_task("Loading data...", total=None)
        
        if not load_csv():
            console.print("❌ CSV loading failed", style="red")
            return False
        
        progress.update(task, completed=100)
    
    console.print("✅ CSV data loaded", style="green")
    
    # Step 3: Validate data
    console.print("\n3️⃣ Validating Data", style="blue")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Validating data...", total=None)
        
        if not validate_data():
            console.print("❌ Data validation failed", style="red")
            return False
        
        progress.update(task, completed=100)
    
    console.print("✅ Data validation completed", style="green")
    
    # Success summary
    console.print("\n🎉 CSV Ingestion Pipeline - SUCCESS!", style="bold green")
    
    success_panel = Panel(
        """✅ CSV ingestion pipeline completed successfully!

📊 Pipeline Summary:
   • Database initialized with staging.test_ingest table
   • CSV data loaded from tests/DB_tests/sample_data.csv
   • Data validated for integrity and quality
   • All records successfully ingested

🚀 Your FANalyze 2.0 CSV ingestion is ready for production!""",
        title="Pipeline Results",
        border_style="green"
    )
    
    console.print(success_panel)
    
    return True


def main():
    """Main function to run the CSV ingestion pipeline."""
    try:
        success = run_csv_ingestion_pipeline()
        return success
    except Exception as e:
        console.print(f"❌ Pipeline execution failed: {e}", style="red")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
