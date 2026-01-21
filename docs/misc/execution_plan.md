# FANalyze 2.0 Execution Plan

## M01 W04: Foundation (Current Focus)
**Goal**: Working mini pipeline with both batch and real-time processing

### Prerequisites
1. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Dependencies**
   ```bash
   uv sync
   ```

3. **Database Setup**
   ```bash
   # Start PostgreSQL via Docker
   docker-compose up -d postgres
   
   # Initialize database schema
   psql -h localhost -U postgres -f sql/init.sql
   ```

### Real-time Pipeline: Synthetic Ticket Sales → PostgreSQL

**Source**: Synthetic ticket sales events (JSON)
**Process**: Row-by-row data collection
**Destination**: PostgreSQL (staging.raw_data)
**Scripts**: `scripts/data_collection/fake_data_generator.py` + `scripts/database/load_to_postgres.py`

#### Step-by-Step Execution:

1. **Generate Synthetic Data**
   ```bash
   # Generate 100 ticket sales events
   uv run python scripts/data_collection/fake_data_generator.py \
     --output data/external/ticket_sales_events.json \
     --count 100
   ```

2. **Load to PostgreSQL**
   ```bash
   # Load events into staging.raw_data table
   uv run python scripts/database/load_to_postgres.py \
     --input data/external/ticket_sales_events.json
   ```

3. **Verify Data**
   ```bash
   # Check data landed correctly
   psql -h localhost -U user_fanalyze_ingest -d postgres -c \
     "SELECT COUNT(*), MAX(created_at) FROM staging.raw_data;"
   ```

**Expected Output**: 100 JSON records in `staging.raw_data` table

### Batch Pipeline: Setlist Data → Snowflake

**Source**: Local JSON files (setlist data)
**Process**: Bulk data collection (500+ rows)
**Destination**: Snowflake
**Scripts**: `scripts/data_collection/api_collector.py` + `scripts/database/load_to_snowflake.py`

#### Step-by-Step Execution:

1. **Collect Setlist Data**
   ```bash
   # Collect Metallica setlists (500+ records)
   uv run python scripts/data_collection/api_collector.py \
     --artist "Metallica" \
     --output data/external/metallica_setlists.json \
     --max-pages 5
   ```

2. **Load to Snowflake**
   ```bash
   # Bulk load setlists into Snowflake
   uv run python scripts/database/load_to_snowflake.py \
     --input data/external/metallica_setlists.json \
     --table STAGING.SETLISTS_RAW
   ```

3. **Verify Data**
   ```bash
   # Check data in Snowflake
   uv run python -c "
   import snowflake.connector
   conn = snowflake.connector.connect(
       user=os.getenv('SNOWFLAKE_USER'),
       account=os.getenv('SNOWFLAKE_ACCOUNT'),
       private_key_file_path=os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH'),
       warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
       database=os.getenv('SNOWFLAKE_DATABASE'),
       schema=os.getenv('SNOWFLAKE_SCHEMA')
   )
   cur = conn.cursor()
   cur.execute('SELECT COUNT(*) FROM STAGING.SETLISTS_RAW')
   print(f'Records in Snowflake: {cur.fetchone()[0]}')
   conn.close()
   "
   ```

**Expected Output**: 500+ setlist records in Snowflake `STAGING.SETLISTS_RAW` table

### Pipeline Integration Test

**End-to-End Validation**:
```bash
# Run both pipelines and verify data flow
uv run python main.py --pipeline realtime
uv run python main.py --pipeline batch

# Verify both databases have data
uv run pytest tests/test_data_pipeline.py -v
```

**Success Criteria**:
- ✅ Real-time: 100+ events in PostgreSQL
- ✅ Batch: 500+ records in Snowflake  
- ✅ Both pipelines run independently
- ✅ Data formats are correct (JSON in PostgreSQL, structured in Snowflake)

---

## M02 W04: Data Processing (Future Planning)
- dbt transformations and data modeling
- Data quality testing and validation
- Warehouse structure optimization

## M03 W04: Real-time & Orchestration (Future Planning)
- Kafka streaming implementation
- Airflow pipeline orchestration
- End-to-end data flow automation

## M04 W04: AI Agent (Future Planning)
- LangGraph agent development
- RAG system with document processing
- Natural language data querying

## M05 W04: Final Integration (Future Planning)
- System testing and validation
- Performance optimization
- Demo preparation and documentation

---

## Troubleshooting

### Common Issues:
1. **PostgreSQL Connection**: Check Docker is running, credentials in .env
2. **Snowflake Connection**: Verify private key path and permissions
3. **Data Format**: Ensure JSON is valid, check file encoding
4. **Environment**: Run `uv run python -c "import os; print(os.getenv('POSTGRES_HOST'))"` to verify env loading

### Debug Commands:
```bash
# Test connections
uv run pytest tests/test_connections.py -v

# Check environment
uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print([k for k in os.environ if 'POSTGRES' in k or 'SNOWFLAKE' in k])"

# Verify data files
ls -la data/external/
file data/external/*.json
```

## Error Handling & Recovery

### Pipeline Failure Recovery:
```bash
# If real-time pipeline fails
uv run python scripts/database/load_to_postgres.py --input data/external/ticket_sales_events.json --retry 3

# If batch pipeline fails
uv run python scripts/database/load_to_snowflake.py --input data/external/metallica_setlists.json --resume

# Check pipeline status
uv run python scripts/monitoring/pipeline_status.py
```

### Data Quality Checks:
```bash
# Validate JSON structure
uv run python scripts/validation/validate_json.py --input data/external/ticket_sales_events.json

# Check data completeness
uv run python scripts/validation/data_completeness.py --source postgres --table staging.raw_data
uv run python scripts/validation/data_completeness.py --source snowflake --table STAGING.SETLISTS_RAW
```

## Performance Monitoring

### Metrics Collection:
```bash
# Monitor pipeline performance
uv run python scripts/monitoring/performance_monitor.py --pipeline realtime
uv run python scripts/monitoring/performance_monitor.py --pipeline batch

# Generate performance report
uv run python scripts/monitoring/generate_report.py --output reports/performance_report.html
```

## Future Module Enhancements

### M02 W04: Data Processing (Detailed Planning)
- **dbt Project Setup**: Initialize dbt project with staging, intermediate, and marts models
- **Data Quality Tests**: Implement dbt tests for data validation
- **Documentation**: Generate dbt docs for data lineage
- **Incremental Models**: Set up incremental processing for large datasets

### M03 W04: Real-time & Orchestration (Detailed Planning)
- **Kafka Setup**: Configure Kafka cluster with topics for ticket sales
- **Airflow DAGs**: Create DAGs for batch and real-time pipeline orchestration
- **Monitoring**: Set up alerts for pipeline failures
- **Scaling**: Configure auto-scaling for high-volume data processing

### M04 W04: AI Agent (Detailed Planning)
- **LangGraph Setup**: Initialize LangGraph agent with conversation memory
- **RAG Implementation**: Set up vector database for document storage
- **API Endpoints**: Create REST API for chatbot interactions
- **Testing**: Implement comprehensive testing for AI responses

### M05 W04: Final Integration (Detailed Planning)
- **End-to-End Testing**: Comprehensive system testing
- **Performance Optimization**: Database indexing, query optimization
- **Security**: Implement authentication and authorization
- **Documentation**: Complete system documentation and user guides