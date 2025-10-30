#!/usr/bin/env python3
"""
Complete CSV Ingestion Test for FANalyze 2.0
Tests the full pipeline: CSV → PostgreSQL → Validation
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from database.csv_loader import main as load_csv
from validation.data_validation import main as validate_data

console = Console()


def test_postgres_connection():
    """Test PostgreSQL connection."""
    try:
        from database.csv_loader import get_postgres_connection
        conn = get_postgres_connection()
        if conn:
            conn.close()
            console.print("✅ PostgreSQL connection successful", style="green")
            return True
        else:
            console.print("❌ PostgreSQL connection failed", style="red")
            return False
    except Exception as e:
        console.print(f"❌ PostgreSQL connection test failed: {e}", style="red")
        return False


def test_csv_file_exists():
    """Test if CSV file exists."""
    csv_path = "sample_data.csv"
    if os.path.exists(csv_path):
        console.print(f"✅ CSV file found: {csv_path}", style="green")
        return True
    else:
        console.print(f"❌ CSV file not found: {csv_path}", style="red")
        return False


def run_complete_test():
    """Run the complete CSV ingestion test."""
    console.print("🚀 FANalyze 2.0 - Complete CSV Ingestion Test", style="bold blue")
    console.print("=" * 60)
    
    # Test 1: Check prerequisites
    console.print("\n1️⃣ Checking Prerequisites", style="blue")
    
    if not test_postgres_connection():
        console.print("❌ Prerequisites check failed", style="red")
        return False
    
    if not test_csv_file_exists():
        console.print("❌ Prerequisites check failed", style="red")
        return False
    
    console.print("✅ Prerequisites check passed", style="green")
    
    # Test 2: Load CSV data
    console.print("\n2️⃣ Loading CSV Data to PostgreSQL", style="blue")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading CSV data...", total=None)
        
        if not load_csv():
            console.print("❌ CSV loading failed", style="red")
            return False
        
        progress.update(task, completed=100)
    
    console.print("✅ CSV data loaded successfully", style="green")
    
    # Test 3: Validate data
    console.print("\n3️⃣ Validating Data Integrity", style="blue")
    
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
    
    # Test 4: Final confirmation
    console.print("\n4️⃣ Final Confirmation", style="blue")
    
    try:
        from database.csv_loader import get_postgres_connection, verify_data_loaded
        
        if verify_data_loaded():
            console.print("✅ Data verification successful", style="green")
        else:
            console.print("❌ Data verification failed", style="red")
            return False
    
    except Exception as e:
        console.print(f"❌ Final confirmation failed: {e}", style="red")
        return False
    
    # Success summary
    console.print("\n🎉 Complete CSV Ingestion Test - SUCCESS!", style="bold green")
    
    success_panel = Panel(
        """✅ All tests passed successfully!

📊 What was accomplished:
   • PostgreSQL connection established
   • CSV file located and processed
   • Data loaded into staging.test_ingest table
   • Data integrity validated
   • Quality metrics calculated
   • Sample data reviewed

🚀 Your FANalyze 2.0 CSV ingestion pipeline is working!""",
        title="Test Results",
        border_style="green"
    )
    
    console.print(success_panel)
    
    return True


def main():
    """Main function to run the complete test."""
    try:
        success = run_complete_test()
        return success
    except Exception as e:
        console.print(f"❌ Test execution failed: {e}", style="red")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
