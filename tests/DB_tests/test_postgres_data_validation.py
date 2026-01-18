#!/usr/bin/env python3
"""
Data Validation Test for FANalyze 2.0 (Postgres)
Tests data integrity and quality validation on Postgres-loaded data
"""

import sys
from pathlib import Path
from rich.console import Console

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from validation.data_validation import main as validate_data

console = Console()


def test_data_validation():
    """Test data validation functionality."""
    console.print(
        "🔍 FANalyze 2.0 - Data Validation Test (Postgres)", style="bold blue"
    )
    console.print("=" * 50)

    try:
        success = validate_data()
        if success:
            console.print("✅ Data validation test passed", style="green")
            return True
        else:
            console.print("❌ Data validation test failed", style="red")
            return False
    except Exception as e:
        console.print(f"❌ Data validation test failed: {e}", style="red")
        return False


def main():
    """Main function to run data validation test."""
    try:
        success = test_data_validation()
        return success
    except Exception as e:
        console.print(f"❌ Test execution failed: {e}", style="red")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
