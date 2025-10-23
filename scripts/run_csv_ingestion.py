#!/usr/bin/env python3
"""
Simple runner script for CSV ingestion
"""

import os
import sys
import subprocess

def main():
    """Run the CSV ingestion script"""
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ingestion_script = os.path.join(script_dir, 'ingest_csv_to_snowflake.py')
    
    # Check if the ingestion script exists
    if not os.path.exists(ingestion_script):
        print(f"Error: Ingestion script not found at {ingestion_script}")
        return False
    
    # Run the ingestion script
    try:
        result = subprocess.run([sys.executable, ingestion_script], 
                              capture_output=True, 
                              text=True, 
                              cwd=script_dir)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running ingestion script: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ CSV ingestion completed successfully!")
    else:
        print("❌ CSV ingestion failed!")
    sys.exit(0 if success else 1)
