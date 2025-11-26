# Airflow Quick Start Guide

## What Was Created

✅ **`docker-compose-airflow.yml`** - Separate compose file for Airflow services
✅ **`airflow/Dockerfile.airflow`** - Custom Airflow image with your dependencies
✅ **`airflow/requirements.txt`** - Python packages needed by Airflow
✅ **`airflow/dags/capstone_data_pipeline.py`** - Example DAG with 5 tasks (meets capstone requirement!)

## First Time Setup

### 1. Set Airflow UID (Linux/Mac only)
```bash
export AIRFLOW_UID=$(id -u)
```

On Windows, you can skip this or set it manually in `.env`:
```bash
AIRFLOW_UID=50000
```

### 2. Start Prerequisites

```bash
cd FANalyze_v2.0

# Start PostgreSQL (if not already running)
docker-compose up -d kafka-postgres

# Start Kafka (if you want to test Kafka DAGs)
docker-compose -f docker-compose-kafka.yml up -d kafka
```

### 3. Start Airflow

```bash
# Build and start Airflow
docker-compose -f docker-compose-airflow.yml up -d --build

# Watch logs
docker-compose -f docker-compose-airflow.yml logs -f
```

### 4. Access Airflow UI

- **URL**: http://localhost:8080
- **Username**: `airflow`
- **Password**: `airflow`

## Verify It's Working

1. **Check containers are running**:
   ```bash
   docker-compose -f docker-compose-airflow.yml ps
   ```

2. **Check DAG appears in UI**:
   - Go to http://localhost:8080
   - You should see `capstone_data_pipeline` DAG

3. **Trigger a test run**:
   - Click on the DAG
   - Click "Play" button to trigger manually
   - Watch it execute!

## Stopping Airflow

```bash
# Stop (keeps data)
docker-compose -f docker-compose-airflow.yml stop

# Stop and remove containers (keeps data)
docker-compose -f docker-compose-airflow.yml down

# Stop and remove everything including volumes
docker-compose -f docker-compose-airflow.yml down -v
```

## Architecture

```
docker-compose.yaml          → PostgreSQL (kafka-postgres)
docker-compose-kafka.yml     → Kafka + Producer/Consumer
docker-compose-airflow.yml   → Airflow (orchestrates everything)
```

All three use the same network: `fa-dae2-capstone_kafka_network`

## Next Steps

1. **Customize the DAG** (`airflow/dags/capstone_data_pipeline.py`):
   - Update paths to match your scripts
   - Add more tasks as needed
   - Configure proper error handling

2. **Add more DAGs**:
   - Create additional DAG files in `airflow/dags/`
   - Airflow will automatically discover them

3. **Configure Connections** (in Airflow UI):
   - Admin → Connections
   - Add Snowflake connection
   - Add PostgreSQL connection

## Troubleshooting

### Port 8080 already in use
```bash
# Change port in docker-compose-airflow.yml:
ports:
  - "8081:8080"  # Use 8081 instead
```

### DAGs not appearing
- Check logs: `docker-compose -f docker-compose-airflow.yml logs scheduler`
- Verify DAG files are in `airflow/dags/`
- Check for Python syntax errors

### Import errors in DAGs
- Ensure all dependencies are in `airflow/requirements.txt`
- Rebuild: `docker-compose -f docker-compose-airflow.yml build`

### Network errors
- Verify network exists: `docker network ls | grep kafka`
- Create if missing: `docker network create fa-dae2-capstone_kafka_network`

## Capstone Requirements Met ✅

- ✅ **Airflow orchestration** with at least 3 tasks
- ✅ **Separate docker-compose file** (modular design)
- ✅ **Connects to existing Kafka/PostgreSQL** (same network)
- ✅ **Ready for batch + streaming pipelines**

Your DAG has **5 tasks**, which exceeds the minimum requirement of 3! 🎉

