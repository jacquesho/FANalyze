# CSV Data Ingestion for FANalyze 2.0

This directory contains scripts for ingesting CSV data into PostgreSQL staging tables, based on the functionality from the M01W03 lab.

## 📁 Files Overview

### Core Scripts
- **`main_csv_ingestion.py`** - Main orchestration script for the complete pipeline
- **`test_csv_ingestion.py`** - Comprehensive test script for the ingestion pipeline
- **`database/csv_loader.py`** - CSV data loader for PostgreSQL
- **`validation/data_validation.py`** - Data validation and quality checks

### Database Setup
- **`sql/init_test_ingest.sql`** - SQL script to create staging.test_ingest table

## 🚀 Quick Start

### 1. Prerequisites
- PostgreSQL running (via Docker or local installation)
- Environment variables configured in `.env`
- CSV file at `tests/DB_tests/sample_data.csv`

### 2. Run the Complete Pipeline
```bash
# Run the complete CSV ingestion pipeline
uv run python scripts/main_csv_ingestion.py
```

### 3. Run Tests Only
```bash
# Run comprehensive tests
uv run python scripts/test_csv_ingestion.py
```

### 4. Individual Components
```bash
# Load CSV data only
uv run python scripts/database/csv_loader.py

# Validate data only
uv run python scripts/validation/data_validation.py
```

## 📊 What the Pipeline Does

1. **Database Initialization**
   - Creates `staging.test_ingest` table
   - Sets up proper permissions and indexes

2. **CSV Data Loading**
   - Reads `tests/DB_tests/sample_data.csv`
   - Loads data into PostgreSQL with conflict resolution
   - Provides progress feedback and error handling

3. **Data Validation**
   - Validates table structure and schema
   - Checks data integrity and quality
   - Identifies null values and duplicates
   - Generates comprehensive reports

4. **Confirmation**
   - Verifies data was loaded correctly
   - Displays sample data for review
   - Provides quality metrics

## 🔧 Configuration

### Environment Variables
```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### CSV File Format
The expected CSV format is:
```csv
id,data_content,file_name
1,Sample CSV data 1,test1.csv
2,Sample CSV data 2,test2.csv
3,Sample CSV data 3,test3.csv
```

## 📋 Database Schema

### staging.test_ingest Table
```sql
CREATE TABLE staging.test_ingest (
    id INTEGER PRIMARY KEY,
    data_content TEXT,
    file_name VARCHAR(255),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

### Run All Tests
```bash
uv run python scripts/test_csv_ingestion.py
```

### Individual Test Components
- **Connection Test**: Verifies PostgreSQL connectivity
- **File Test**: Checks if CSV file exists
- **Loading Test**: Tests CSV data loading
- **Validation Test**: Tests data integrity checks
- **Confirmation Test**: Verifies final data state

## 🐛 Troubleshooting

### Common Issues
1. **PostgreSQL Connection**: Check Docker is running and credentials are correct
2. **CSV File**: Ensure `tests/DB_tests/sample_data.csv` exists
3. **Permissions**: Verify database user has proper permissions
4. **Environment**: Check that `.env` file is properly configured

### Debug Commands
```bash
# Test PostgreSQL connection
uv run python -c "from scripts.database.csv_loader import get_postgres_connection; print('Connection:', get_postgres_connection())"

# Check CSV file
ls -la tests/DB_tests/sample_data.csv

# Verify environment
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print([k for k in os.environ if 'POSTGRES' in k])"
```

## 📚 Integration with FANalyze 2.0

This CSV ingestion functionality integrates with the broader FANalyze 2.0 architecture:

- **Real-time Pipeline**: CSV data can be processed alongside real-time ticket sales
- **Batch Pipeline**: CSV data can be loaded into Snowflake for analytics
- **Data Quality**: Validation ensures data integrity across the platform
- **Monitoring**: Progress tracking and error handling for production use

## 🎯 Next Steps

After successful CSV ingestion:
1. **Data Processing**: Use dbt for transformations in Module 02
2. **Analytics**: Load data into Snowflake for advanced analytics
3. **AI Integration**: Use data for LangGraph agent training in Module 04
4. **Production**: Scale to handle larger datasets and real-time processing
