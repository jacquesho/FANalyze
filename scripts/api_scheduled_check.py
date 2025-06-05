from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.utils.dates import days_ago
from datetime import datetime
import pendulum

# DAG Defaults
default_args = {"owner": "airflow"}
local_tz = pendulum.timezone("Asia/Ho_Chi_Minh")

with DAG(
    dag_id="scheduled_check",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=["fanalyze", "scheduled"],
) as dag:

    def get_latest_and_build_command():
        hook = SnowflakeHook(snowflake_conn_id="fanalyze_conn")
        sql = "SELECT MAX(latest_known_show) FROM DB_FANALYZE.FANALYZE.DIM_LATEST_SHOW_PER_ARTIST"
        records = hook.get_first(sql)
        start_date = records[0].strftime("%Y-%m-%d") if records[0] else "2025-01-01"

        end_date = datetime.today().strftime("%Y-%m-%d")
        print(f"Scheduled fetch: {start_date} to {end_date}")

        return f"""python /opt/airflow/scripts/api_sche
        duled_check.py \
--outdir /opt/airflow/models/01_staging/setlistfm_data \
--show_prefix Update_ --setlist_prefix Update_ \
--start_date {start_date} --end_date {end_date}"""

    fetch_recent_shows = BashOperator(
        task_id="fetch_recent_shows",
        bash_command="{{ task_instance.xcom_pull(task_ids='build_api_command') }}",
    )

    build_api_command = PythonOperator(
        task_id="build_api_command", python_callable=get_latest_and_build_command
    )

    build_api_command >> fetch_recent_shows
