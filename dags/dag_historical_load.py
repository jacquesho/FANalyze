from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from upload_setlists_to_stage import upload_setlists_to_stage
from datetime import datetime
from pathlib import Path
import os

# ── Base paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
KAFKA_SCRIPTS_DIR = Path("/opt/airflow/dags/scripts/kafka")
STAGING_DIR = PROJECT_ROOT / "models" / "01_staging" / "setlistfm_data"
SQL_DIR = Path(__file__).resolve().parent / "sql"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "api_setlistfm.py"
PYTHON_EXECUTABLE = "/home/airflow/.local/bin/python"

os.makedirs(STAGING_DIR, exist_ok=True)

with DAG(
    dag_id="historical_staging_load",
    start_date=datetime(2025, 5, 1),
    schedule_interval=None,
    catchup=False,
    template_searchpath=[str(SQL_DIR)],
) as dag:
    fetch_data = BashOperator(
        task_id="run_api_setlist",
        bash_command=f"python {SCRIPT_PATH} --outdir {STAGING_DIR}",
    )

    def list_staging_files(ti):
        csvs = list(STAGING_DIR.rglob("*_shows.csv"))
        jsons = list(STAGING_DIR.rglob("*.json"))
        if not csvs:
            raise FileNotFoundError(f"No CSV files found in {STAGING_DIR}")
        if not jsons:
            raise FileNotFoundError(f"No JSON files found in {STAGING_DIR}")
        ti.xcom_push(key="csv_files", value=[str(p) for p in csvs])
        ti.xcom_push(key="json_files", value=[str(p) for p in jsons])

    prep_files = PythonOperator(
        task_id="list_staging_files",
        python_callable=list_staging_files,
    )

    load_shows = SnowflakeOperator(
        task_id="copy_shows_to_stage",
        snowflake_conn_id="SF_JHo_connection",
        sql="insert_his_shows.sql",
    )

    upsert_latest_show_per_artist = SnowflakeOperator(
        task_id="upsert_latest_show_per_artist",
        snowflake_conn_id="SF_JHo_connection",
        sql="sql/upsert_dim_latest_show.sql",
    )

    upload_setlists_to_stage = PythonOperator(
        task_id="upload_setlists_to_stage",
        python_callable=upload_setlists_to_stage,
        dag=dag,
    )

    insert_setlists = SnowflakeOperator(
        task_id="insert_setlists_from_stage",
        snowflake_conn_id="SF_JHo_connection",
        sql="insert_his_setlists.sql",
    )

    produce_to_kafka = BashOperator(
        task_id="produce_historical_to_kafka",
        bash_command=f"{PYTHON_EXECUTABLE} /opt/airflow/dags/scripts/kafka/producer_shows.py --mode historical",
    )

    consume_from_kafka = BashOperator(
        task_id="consume_historical_from_kafka",
        bash_command=f"{PYTHON_EXECUTABLE} {KAFKA_SCRIPTS_DIR / 'consumer_shows.py'} --mode historical",
    )

    (
        fetch_data
        >> prep_files
        >> load_shows
        >> upsert_latest_show_per_artist
        >> upload_setlists_to_stage
        >> insert_setlists
        >> produce_to_kafka
        >> consume_from_kafka
    )
