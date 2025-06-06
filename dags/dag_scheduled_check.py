from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime, timedelta
from pathlib import Path

# ── Base paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/opt/airflow")  # Use absolute path in container
STAGING_DIR = PROJECT_ROOT / "models/01_staging/setlistfm_data"
SQL_DIR = PROJECT_ROOT / "dags/sql"
SCRIPT_PATH = PROJECT_ROOT / "scripts/api_scheduled_check.py"

default_args = {
    "owner": "fanalyze",
    "start_date": datetime(2025, 6, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def list_csv_files(**kwargs):
    dir_path = Path("/opt/airflow/models/01_staging/setlistfm_data")
    print(f"🔍 Searching for CSVs in: {dir_path}")
    print(f"Directory exists: {dir_path.exists()}")

    csv_files = sorted(dir_path.glob("Update_*.csv"))

    if not csv_files:
        print("⚠️ No matching CSV files found in:", dir_path)
        # List all files in directory to debug
        if dir_path.exists():
            print("📁 Directory contents:")
            for f in dir_path.iterdir():
                print(f"  - {f.name}")
    else:
        print("✅ Found files:")
        for f in csv_files:
            print("-", f)

    file_paths = [str(f.resolve()) for f in csv_files]
    return file_paths  # Airflow will push this to XCom


def print_date_range(**context):
    try:
        result = context["ti"].xcom_pull(
            task_ids="get_latest_show_date", key="return_value"
        )
        print("🔍 Raw XCom result:", result)

        if not result:
            raise ValueError("No data returned from get_latest_show_date")

        if isinstance(result, list) and len(result) > 0:
            latest_date = result[0].get("LATEST_DATE") or result[0].get(
                "LATEST_DATE".lower()
            )
            if not latest_date:
                raise ValueError("LATEST_DATE not found in result")
        else:
            raise ValueError(f"Unexpected result format: {result}")

        print(f"Start: {latest_date}, End: {context['ds']}")
    except Exception as e:
        print(f"⚠️ Error in debug_date_range: {str(e)}")
        raise


def debug_fetch_summary(**kwargs):
    shows = kwargs.get("shows", [])
    csv_output_path = kwargs.get("csv_output_path", "<not provided>")
    json_output_path = kwargs.get("json_output_path", "<not provided>")

    print(f"🎵 Found {len(shows)} shows")
    print(f"📁 Writing CSV to: {csv_output_path}")
    print(f"📝 Writing JSON to: {json_output_path}")


with DAG(
    dag_id="Scheduled_Show_Check",
    default_args=default_args,
    schedule_interval="@weekly",
    catchup=False,
    description="Scheduled check for new shows and setlists",
    tags=["fanalyze", "scheduled"],
    template_searchpath=[str(SQL_DIR)],
) as dag:
    get_latest_show_date = SnowflakeOperator(
        task_id="get_latest_show_date",
        sql="get_latest_show_date.sql",
        snowflake_conn_id="SF_JHo_connection",
        params={"artist_id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"},
        do_xcom_push=True,
    )

    debug_date_range = PythonOperator(
        task_id="debug_date_range",
        python_callable=print_date_range,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_new_data = BashOperator(
        task_id="fetch_recent_shows",
        bash_command=(
            "python {{ params.script_path }} "
            "--outdir {{ params.outdir }} "
            "--show_prefix Update_ "
            "--setlist_prefix Update_ "
            "--start_date {{ ti.xcom_pull(task_ids='get_latest_show_date')[0]['LATEST_DATE'] }} "
            "--end_date {{ ds }} "
            "|| echo 'Command failed with status $?'"
        ),
        params={
            "script_path": SCRIPT_PATH,
            "outdir": STAGING_DIR,
        },
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

    check_script = BashOperator(
        task_id="check_script",
        bash_command=f'ls -l {SCRIPT_PATH} || echo "Script not found!"',
    )

    # Update your task dependencies
    (
        get_latest_show_date
        >> debug_date_range
        >> check_script  # Add this task
        >> fetch_new_data
        >> refresh_lookup
        >> list_csv_files
        >> [insert_shows, insert_setlists]
    )
