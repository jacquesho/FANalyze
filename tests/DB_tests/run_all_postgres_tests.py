#!/usr/bin/env python3
"""
Main Test Runner for FANalyze 2.0 Postgres Tests
Runs all Postgres-related tests in sequence
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from test_postgres_csv_ingestion import main as test_csv_ingestion
from test_postgres_data_validation import main as test_data_validation
from test_postgres_pipeline_integration import main as test_pipeline_integration

console = Console()


def run_all_postgres_tests():
    """Run all Postgres tests in sequence."""
    console.print("🚀 FANalyze 2.0 - Postgres Test Suite", style="bold blue")
    console.print("=" * 60)
    
    tests = [
        ("CSV Ingestion Test", test_csv_ingestion),
        ("Data Validation Test", test_data_validation),
        ("Pipeline Integration Test", test_pipeline_integration),
    ]
    
    results = []
    
    for i, (test_name, test_func) in enumerate(tests, 1):
        console.print(f"\n{i}️⃣ Running {test_name}", style="blue")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {test_name}...", total=None)
            
            try:
                success = test_func()
                results.append((test_name, success))
                
                if success:
                    console.print(f"✅ {test_name} passed", style="green")
                else:
                    console.print(f"❌ {test_name} failed", style="red")
                
                progress.update(task, completed=100)
                
            except Exception as e:
                console.print(f"❌ {test_name} failed with error: {e}", style="red")
                results.append((test_name, False))
                progress.update(task, completed=100)
    
    # Summary
    console.print("\n📊 Test Results Summary", style="bold blue")
    console.print("=" * 40)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        console.print(f"{test_name}: {status}", style="green" if success else "red")
    
    console.print(f"\nOverall: {passed}/{total} tests passed", style="bold green" if passed == total else "bold red")
    
    # Final result
    if passed == total:
        success_panel = Panel(
            f"""✅ All Postgres tests passed successfully!

📊 Test Summary:
   • CSV Ingestion: ✅ PASSED
   • Data Validation: ✅ PASSED  
   • Pipeline Integration: ✅ PASSED

🚀 Your FANalyze 2.0 Postgres functionality is working perfectly!""",
            title="Test Results",
            border_style="green"
        )
        console.print(success_panel)
        return True
    else:
        error_panel = Panel(
            f"""❌ Some Postgres tests failed!

📊 Test Summary:
   • Passed: {passed}/{total}
   • Failed: {total - passed}/{total}

🔧 Please check the failed tests and fix any issues before proceeding.""",
            title="Test Results",
            border_style="red"
        )
        console.print(error_panel)
        return False


def main():
    """Main function to run all Postgres tests."""
    try:
        success = run_all_postgres_tests()
        return success
    except Exception as e:
        console.print(f"❌ Test suite execution failed: {e}", style="red")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


