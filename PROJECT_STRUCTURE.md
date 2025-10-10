# FANalyze 2.0 - Project Structure

## 📁 Updated Project Organization

### ✅ Better Structure (Current)
```
FANalyze_v2.0/
├── 📄 README.md                    # Project documentation
├── 📄 pyproject.toml              # UV project configuration
├── 📄 docker-compose.yaml         # Docker services configuration
├── 📄 .env.example                # Environment variables template
├── 📄 .gitignore                  # Git ignore patterns
├── 📁 config/                     # Configuration files
│   └── 📄 settings.py             # Application settings
├── 📁 docs/                       # Documentation
│   └── 📄 execution_plan.md       # Detailed implementation plan
├── 📁 scripts/                    # Data processing scripts
│   ├── 📁 database/              # Database operations
│   │   └── 📄 csv_loader.py       # CSV data loader
│   ├── 📁 validation/            # Data quality checks
│   │   └── 📄 data_validation.py # Data validation
│   └── 📄 main_csv_ingestion.py  # Main orchestration script
├── 📁 tests/                      # Test suite
│   ├── 📁 DB_connections/        # Test data files
│   │   └── 📄 sample_data.csv    # Sample CSV data
│   └── 📁 DB_tests/              # Database tests
│       ├── 📄 test_csv_ingestion.py
│       ├── 📄 test_data_validation.py
│       ├── 📄 test_pipeline_integration.py
│       ├── 📄 run_all_tests.py
│       └── 📄 README.md
├── 📁 sql/                        # SQL scripts
│   └── 📄 init_test_ingest.sql    # Database initialization
└── 📄 main.py                     # Main pipeline orchestrator
```

## 🎯 Key Improvements

### 1. **Better File Organization**
- **Tests in `/tests`** - Standard Python convention
- **Scripts in `/scripts`** - Reusable utilities
- **Test data with tests** - Related files together
- **Clear separation** - Tests vs. production code

### 2. **User Management**
- **`user_fanalyze_ingest`** - Dedicated user for data ingestion
- **Proper permissions** - Schema and table access
- **Security** - Isolated user for data operations
- **Backward compatibility** - `staging_user` still supported

### 3. **Test Structure**
- **`DB_tests/`** - All database-related tests
- **Individual test files** - Focused testing
- **Test runner** - Comprehensive test execution
- **Documentation** - Clear test guidelines

## 🚀 Usage Examples

### Run Individual Tests
```bash
# Test CSV ingestion
uv run python tests/DB_tests/test_csv_ingestion.py

# Test data validation
uv run python tests/DB_tests/test_data_validation.py

# Test pipeline integration
uv run python tests/DB_tests/test_pipeline_integration.py
```

### Run All Database Tests
```bash
# Run all database tests
uv run python tests/DB_tests/run_all_tests.py

# Or using pytest
uv run python -m pytest tests/DB_tests/ -v
```

### Run Production Scripts
```bash
# Run CSV ingestion pipeline
uv run python scripts/main_csv_ingestion.py

# Run individual components
uv run python scripts/database/csv_loader.py
uv run python scripts/validation/data_validation.py
```

## 🔧 Configuration

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
```bash
# Initialize database
psql -h localhost -U postgres -f sql/init_test_ingest.sql

# Verify user creation
psql -h localhost -U postgres -c "SELECT rolname FROM pg_roles WHERE rolname = 'user_fanalyze_ingest';"
```

## 📊 Test Categories

### Current Tests
- **CSV Ingestion** - Complete CSV data loading pipeline
- **Data Validation** - Data integrity and quality checks
- **Pipeline Integration** - End-to-end pipeline testing

### Future Tests (Planned)
- **Snowflake Ingestion** - Snowflake data loading tests
- **PostgreSQL to Snowflake** - Data transfer tests
- **Performance Tests** - Load and stress testing
- **Data Quality Tests** - Advanced quality validation

## 🎯 Benefits

### 1. **Scalability**
- Easy to add new test types
- Clear separation of concerns
- Reusable components

### 2. **Maintainability**
- Organized file structure
- Clear documentation
- Standard conventions

### 3. **Security**
- Dedicated database user
- Proper permissions
- Isolated operations

### 4. **Testing**
- Comprehensive test coverage
- Individual and integrated tests
- Clear test organization

## 🚀 Next Steps

### Immediate
1. **Test the new structure** - Verify all tests work
2. **Update documentation** - Ensure all paths are correct
3. **Validate user permissions** - Test database access

### Future
1. **Add Snowflake tests** - When ready for Snowflake integration
2. **Add transfer tests** - PostgreSQL to Snowflake testing
3. **Add performance tests** - Load and stress testing
4. **CI/CD integration** - Automated testing pipeline

## 📚 Integration with FANalyze 2.0

This structure integrates seamlessly with the broader FANalyze 2.0 architecture:

- **Real-time Pipeline** - Tests validate real-time data ingestion
- **Batch Pipeline** - Tests ensure batch data processing
- **Data Quality** - Tests verify data integrity
- **Performance** - Tests ensure system scalability
- **Monitoring** - Tests validate observability

The new structure provides a solid foundation for scaling the FANalyze 2.0 project with comprehensive testing and clear organization.
