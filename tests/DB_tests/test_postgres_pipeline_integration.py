#!/usr/bin/env python3
"""
Pipeline Integration Test for FANalyze 2.0 (Postgres)
Tests the complete data pipeline integration against Postgres
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from database.csv_loader import main as load_csv
from validation.data_validation import main as validate_data

console = Console()


def test_pipeline_integration():
    """Test complete pipeline integration."""
    console.print("🔄 FANalyze 2.0 - Pipeline Integration Test (Postgres)", style="bold blue")
    console.print("=" * 60)
    
    # Step 1: Load CSV data
    console.print("\n1️⃣ Loading CSV Data", style="blue")
    if not load_csv():
        console.print("❌ CSV loading failed", style="red")
        return False
    console.print("✅ CSV loading successful", style="green")
    
    # Step 2: Validate data
    console.print("\n2️⃣ Validating Data", style="blue")
    if not validate_data():
        console.print("❌ Data validation failed", style="red")
        return False
    console.print("✅ Data validation successful", style="green")
    
    # Step 3: Integration verification
    console.print("\n3️⃣ Integration Verification", style="blue")
    try:
        from database.csv_loader import get_postgres_connection, verify_data_loaded
        
        if verify_data_loaded():
            console.print("✅ Integration verification successful", style="green")
        else:
            console.print("❌ Integration verification failed", style="red")
            return False
    
    except Exception as e:
        console.print(f"❌ Integration verification failed: {e}", style="red")
        return False
    
    # Success summary
    console.print("\n🎉 Pipeline Integration Test - SUCCESS!", style="bold green")
    
    success_panel = Panel(
        """✅ Pipeline integration test passed!

📊 Integration Summary:
   • CSV data loading pipeline working
   • Data validation pipeline working
   • End-to-end integration successful
   • All components communicating properly

🚀 Your FANalyze 2.0 pipeline is fully integrated!""",
        title="Integration Test Results",
        border_style="green"
    )
    
    console.print(success_panel)
    
    return True


def main():
    """Main function to run pipeline integration test."""
    try:
        success = test_pipeline_integration()
        return success
    except Exception as e:
        console.print(f"❌ Test execution failed: {e}", style="red")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


