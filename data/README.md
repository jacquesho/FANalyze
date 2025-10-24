# Data Directory Structure

This directory contains all data files for the FANalyze project.

## 📁 Directory Structure

```
data/
├── raw/                    # Raw, unprocessed data
│   ├── csv/                # CSV files for ingestion
│   │   ├── all_shows_2015_to_2025_with_tickets.csv
│   │   └── real_us_future_concerts_current_sales_2025_2026.csv
│   ├── json/               # JSON files (if any)
│   └── api/                # API data (if any)
├── external/               # External data sources
│   └── staging_json/       # JSONL files from APIs
└── processed/              # Processed data (if needed)
```

## 🎯 **Data Flow**

1. **Raw Data**: CSV files go in `data/raw/csv/`
2. **Ingestion**: Scripts read from `data/raw/csv/` and load to Snowflake
3. **Processing**: dbt models transform raw data into analytics tables
4. **Analytics**: Final marts are available in Snowflake

## 📋 **File Naming Convention**

- **Raw Data**: `{entity}_{timeframe}_{description}.csv`
- **Examples**: 
  - `all_shows_2015_to_2025_with_tickets.csv`
  - `real_us_future_concerts_current_sales_2025_2026.csv`

## 🚀 **Usage**

```bash
# Place your CSV files in data/raw/csv/
# Run the ingestion script
cd scripts/
python3 ingest_csv_shows__snowflake.py
```
