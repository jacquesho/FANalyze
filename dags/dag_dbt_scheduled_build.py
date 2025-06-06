from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'fanalyze',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='Scheduled_dbt_Run',
    default_args=default_args,
    description='Run dbt build on a schedule',
    schedule_interval='@hourly',  # or '0 6 * * *' for daily at 6am UTC
    start_date=datetime(2024, 6, 1),
    catchup=False,
    tags=['dbt'],
) as dag:

    run_dbt = BashOperator(
        task_id='run_dbt_build',
        bash_command='cd /opt/airflow/dbt && dbt build --project-dir .',
    )
