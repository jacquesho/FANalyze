# Database Tests for FANalyze 2.0

This directory contains all database-related tests for the FANalyze 2.0 project.

## 📁 Test Structure

### Test Categories
- **`test_postgres_csv_ingestion.py`** - Complete CSV ingestion pipeline testing (Postgres)
- **`test_postgres_data_validation.py`** - Data integrity and quality validation (Postgres)
- **`test_postgres_pipeline_integration.py`** - End-to-end pipeline integration (Postgres)
- **`test_connections_postgres.py`** - Postgres connectivity smoke test
- **`test_connections_snowflake.py`** - Snowflake connectivity smoke test

### Test Data
- **`sample_data.csv`** - Sample CSV data for testing

## 🚀 Running Tests

### Individual Tests
```bash
# Test Postgres CSV ingestion
uv run python tests/DB_tests/test_postgres_csv_ingestion.py

# Test Postgres data validation
uv run python tests/DB_tests/test_postgres_data_validation.py

# Test Postgres pipeline integration
uv run python tests/DB_tests/test_postgres_pipeline_integration.py

# Check Postgres connectivity
uv run python -m pytest tests/DB_tests/test_connections_postgres.py -q

# Check Snowflake connectivity
uv run python -m pytest tests/DB_tests/test_connections_snowflake.py -q
```

### All Postgres Tests
```bash
# Run the Postgres test suite orchestrator
uv run python tests/DB_tests/run_all_postgres_tests.py

# Or run via pytest
uv run python -m pytest tests/DB_tests/ -v -k postgres
```

## 🔧 Test Configuration

### Environment Variables
```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=user_fanalyze_ingest
POSTGRES_PASSWORD=fanalyze_ingest_password
```

### Database Setup
Tests require the following database setup:
- PostgreSQL running
- `staging.test_ingest` table created
- `user_fanalyze_ingest` user with proper permissions

## 📊 Test Coverage

### CSV Ingestion Tests
- ✅ PostgreSQL connection testing
- ✅ CSV file existence validation
- ✅ Data loading verification
- ✅ Data integrity checks
- ✅ Sample data display

### Data Validation Tests
- ✅ Table structure validation
- ✅ Data integrity checks
- ✅ Null value detection
- ✅ Duplicate identification
- ✅ Quality metrics calculation

### Pipeline Integration Tests
- ✅ End-to-end pipeline testing
- ✅ Component integration verification
- ✅ Data flow validation
- ✅ Error handling testing

## 🎯 Future Test Categories

### Planned Tests
- **`test_snowflake_ingestion.py`** - Snowflake data loading tests
- **`test_postgres_to_snowflake.py`** - PostgreSQL to Snowflake transfer tests
- **`test_data_quality.py`** - Advanced data quality testing
- **`test_performance.py`** - Performance and load testing

### Test Framework
- **`conftest.py`** - Pytest configuration and fixtures
- **`test_utilities.py`** - Shared test utilities and helpers
- **`test_data/`** - Test data files and fixtures

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
2. **User Permissions**: Verify `user_fanalyze_ingest` user has proper permissions
3. **Test Data**: Ensure `sample_data.csv` exists in the correct location
4. **Environment**: Check that `.env` file is properly configured

### Debug Commands
```bash
# Test database connection
uv run python -c "from scripts.database.csv_loader import get_postgres_connection; print('Connection:', get_postgres_connection())"

# Check test data
ls -la tests/DB_tests/sample_data.csv

# Verify environment
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print([k for k in os.environ if 'POSTGRES' in k])"
```

## 📚 Integration with FANalyze 2.0

This test structure integrates with the broader FANalyze 2.0 architecture:

- **Real-time Pipeline**: Tests validate real-time data ingestion
- **Batch Pipeline**: Tests ensure batch data processing works correctly
- **Data Quality**: Tests verify data integrity across the platform
- **Performance**: Tests ensure system can handle expected data volumes
- **Monitoring**: Tests validate observability and error handling

## 🎯 Next Steps

After successful database testing:
1. **Snowflake Tests**: Add Snowflake data loading tests
2. **Transfer Tests**: Add PostgreSQL to Snowflake transfer tests
3. **Performance Tests**: Add load and stress testing
4. **CI/CD Integration**: Integrate tests with automated pipelines
