#!/bin/bash

echo "🚀 FANalyze CSV Batch Ingestion Script"
echo "======================================"

# Set variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/ingest_csv_to_snowflake.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: Python ingestion script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if CSV files exist
CSV_FILES=(
    "$PROJECT_DIR/all_shows_2015_to_2025_with_tickets.csv"
    "$PROJECT_DIR/real_us_future_concerts_2025_2026.csv"
    "$PROJECT_DIR/real_us_future_concerts_current_sales_2025_2026.csv"
)

echo "📁 Checking for CSV files..."
for file in "${CSV_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found: $(basename "$file")"
    else
        echo "⚠️  Missing: $(basename "$file")"
    fi
done

echo ""
echo "🐍 Running Python ingestion script..."
cd "$SCRIPT_DIR"

# Run the Python script
python3 "$PYTHON_SCRIPT"

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Batch ingestion completed successfully!"
    echo ""
    echo "📊 Next steps:"
    echo "1. Run 'dbt run' to build your models"
    echo "2. Run 'dbt test' to validate data quality"
    echo "3. Check your Snowflake tables in FAN_RAW schema"
else
    echo ""
    echo "❌ Batch ingestion failed!"
    echo "Check the logs above for error details."
    exit 1
fi
