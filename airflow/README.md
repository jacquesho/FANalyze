# Airflow Setup for FANalyze v2.0

This directory contains Airflow configuration and DAGs for orchestrating data pipelines.

## Directory Structure

```
airflow/
├── dags/              # DAG definitions
├── logs/              # Airflow execution logs
├── config/            # Airflow configuration files
├── plugins/           # Custom Airflow plugins
├── Dockerfile.airflow # Docker image for Airflow
└── requirements.txt   # Python dependencies
```

## Quick Start

### Prerequisites

1. **Network exists**: Ensure the Docker network is created:
   ```bash
   docker network create fa-dae2-capstone_kafka_network
   ```

2. **PostgreSQL running**: Start PostgreSQL from main compose:
   ```bash
   docker-compose up -d kafka-postgres
   ```

3. **Kafka running** (optional, for Kafka DAGs):
   ```bash
   docker-compose -f docker-compose-kafka.yml up -d kafka
   ```

### Start Airflow

```bash
# Set Airflow UID (Linux/Mac)
export AIRFLOW_UID=$(id -u)

# Start Airflow
docker-compose -f docker-compose-airflow.yml up -d

# Check status
docker-compose -f docker-compose-airflow.yml ps
```

### Access Airflow UI

- **URL**: http://localhost:8080
- **Username**: `airflow`
- **Password**: `airflow` (default, change in production!)

### Stop Airflow

```bash
docker-compose -f docker-compose-airflow.yml down
```

## Environment Variables

Airflow will use variables from your `.env` file for:
- PostgreSQL connections (`POSTGRES_*`)
- Snowflake connections (`SNOWFLAKE_*`)
- Kafka connections (`KAFKA_BOOTSTRAP_SERVERS`)

## Creating DAGs

Place your DAG files in `airflow/dags/`. They will be automatically discovered by Airflow.

Example DAG structure:
```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="my_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
) as dag:
    task1 = BashOperator(
        task_id="ingest_data",
        bash_command="python /opt/airflow/scripts/my_script.py"
    )
    
    task2 = BashOperator(
        task_id="transform_data",
        bash_command="dbt run --project-dir /opt/airflow/dbt"
    )
    
    task1 >> task2
```

## Troubleshooting

### Airflow won't start
- Check if port 8080 is available
- Verify network exists: `docker network ls | grep kafka`
- Check logs: `docker-compose -f docker-compose-airflow.yml logs`

### DAGs not appearing
- Check DAG files are in `airflow/dags/`
- Verify file permissions
- Check Airflow logs for parsing errors

### Connection errors
- Verify `.env` file has correct credentials
- Check network connectivity between containers
- Ensure PostgreSQL/Kafka are running

## Next Steps

1. Create DAGs in `airflow/dags/` for:
   - Batch CSV ingestion
   - Kafka producer/consumer orchestration
   - dbt transformations
   - Data validation

2. Configure connections in Airflow UI:
   - Snowflake connection
   - PostgreSQL connection
   - Kafka connection (if needed)

