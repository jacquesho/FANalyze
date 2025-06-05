from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime, timedelta
from pathlib import Path

# ── Base paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # /opt/airflow
STAGING_DIR = PROJECT_ROOT / "models" / "01_staging" / "setlistfm_data"
SQL_DIR = Path(__file__).resolve().parent / "sql"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "api_scheduled_check.py"

default_args = {
    "owner": "fanalyze",
    "start_date": datetime(2025, 6, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def list_csv_files(**kwargs):
    dir_path = Path("/opt/airflow/models/01_staging/setlistfm_data")
    csv_files = sorted(dir_path.glob("Update_*.csv"))

    if not csv_files:
        print("⚠️ No matching CSV files found in:", dir_path)
    else:
        print("✅ Found files:")
        for f in csv_files:
            print("-", f)

    file_paths = [str(f.resolve()) for f in csv_files]
    return file_paths  # Airflow will push this to XCom


with DAG(
    dag_id="scheduled_check",
    default_args=default_args,
    schedule_interval="@weekly",
    catchup=False,
    description="Scheduled check for new shows and setlists",
    tags=["fanalyze", "scheduled"],
    template_searchpath=[str(SQL_DIR)],
) as dag:
    fetch_new_data = BashOperator(
        task_id="fetch_recent_shows",
        bash_command=f"python {SCRIPT_PATH} --outdir {STAGING_DIR} --show_prefix Update_ --setlist_prefix Update_",
    )

    refresh_lookup = SnowflakeOperator(
        task_id="refresh_latest_show_per_artist",
        snowflake_conn_id="SF_JHo_connection",
        sql="refresh_dim_latest_show.sql",
    )

    list_csv_files = PythonOperator(
        task_id="list_csv_files",
        python_callable=list_csv_files,
        provide_context=True,
    )

    insert_shows = SnowflakeOperator(
        task_id="insert_new_shows",
        snowflake_conn_id="SF_JHo_connection",
        sql="insert_sch_shows.sql",
    )

    insert_setlists = SnowflakeOperator(
        task_id="insert_new_setlists",
        snowflake_conn_id="SF_JHo_connection",
        sql="insert_sch_setlists.sql",
    )

    produce_historical = BashOperator(
        task_id="produce_historical_shows",
        bash_command="python /opt/airflow/dags/scripts/produce_shows.py --mode historical",
        dag=dag,
    )

    (
        fetch_new_data
        >> refresh_lookup
        >> list_csv_files
        >> [insert_shows, insert_setlists]
        >> produce_historical
    )
