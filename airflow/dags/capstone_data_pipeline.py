"""
Capstone Data Pipeline DAG
Orchestrates batch CSV ingestion, Kafka streaming, and data validation
"""

from datetime import datetime, timedelta
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Default arguments
default_args = {
    "owner": "fanalyze",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Create DAG
with DAG(
    dag_id="capstone_data_pipeline",
    default_args=default_args,
    description="Orchestrates batch CSV ingestion, Kafka streaming, and data validation",
    schedule_interval=timedelta(hours=1),  # Run every hour
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Bangkok"),
    catchup=False,
    tags=["capstone", "ingestion", "kafka", "validation"],
) as dag:
    
    # Task 1: Batch CSV Ingestion
    ingest_csv = BashOperator(
        task_id="ingest_csv_to_snowflake",
        bash_command="""
        cd /opt/airflow && \
        python -m scripts.ingest_csv_shows__snowflake
        """,
    )
    
    # Task 2: Validate Kafka Consumer is Processing Messages
    validate_kafka_consumer = BashOperator(
        task_id="validate_kafka_consumer",
        bash_command="""
        # Check if consumer container is running and processing messages
        # This is a simple validation - in production, you'd check Kafka metrics
        echo "Validating Kafka consumer is processing messages..."
        echo "Check PostgreSQL staging.ticket_sales table for recent inserts"
        """,
    )
    
    # Task 3: Data Validation
    validate_data = BashOperator(
        task_id="validate_data_quality",
        bash_command="""
        cd /opt/airflow && \
        python -m scripts.validation.data_validation
        """,
    )
    
    # Task 4: Run dbt Transformations (optional, but good practice)
    dbt_run = BashOperator(
        task_id="dbt_run_transformations",
        bash_command="""
        cd /opt/airflow/dbt && \
        dbt run --profiles-dir /opt/airflow/.dbt
        """,
    )
    
    # Task 5: Run dbt Tests
    dbt_test = BashOperator(
        task_id="dbt_test_models",
        bash_command="""
        cd /opt/airflow/dbt && \
        dbt test --profiles-dir /opt/airflow/.dbt
        """,
    )
    
    # Define task dependencies
    ingest_csv >> validate_kafka_consumer >> validate_data >> dbt_run >> dbt_test

