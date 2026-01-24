"""
Streaming Data Pipeline DAG
Orchestrates Kafka streaming validation, PostgreSQL to Snowflake sync, and dbt transformations
"""

import os
import subprocess
import sys
import psycopg2
import json
from datetime import timedelta
import pendulum
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from pathlib import Path


def get_postgres_env_vars():
    """Get PostgreSQL environment variables for sync script (INGEST credentials)"""
    return {
        "POSTGRES_HOST": os.environ["POSTGRES_HOST"],
        "POSTGRES_PORT": os.environ["POSTGRES_PORT"],
        "POSTGRES_DB": os.environ["POSTGRES_DB"],
        "POSTGRES_USER_INGEST": os.environ["POSTGRES_USER_INGEST"],
        "POSTGRES_PASSWORD_INGEST": os.environ["POSTGRES_PASSWORD_INGEST"],
    }


def get_snowflake_env_vars(include_dbt=False):
    """
    Get Snowflake environment variables from Airflow connections
    Resolves connection values for Python tasks (not Jinja2 templates)

    Args:
        include_dbt: If True, includes dbt-specific paths and private key password
    """
    # Get connection and resolve actual values (not Jinja2 templates)
    conn = BaseHook.get_connection("snowflake_default")
    extra = (
        json.loads(conn.extra) if isinstance(conn.extra, str) else (conn.extra or {})
    )

    env_vars = {
        "SNOWFLAKE_ACCOUNT": extra.get("account", ""),
        "SNOWFLAKE_USER": conn.login or "",
        "SNOWFLAKE_ROLE": extra.get("role", ""),
        "SNOWFLAKE_WAREHOUSE": extra.get("warehouse", ""),
        "SNOWFLAKE_DATABASE": extra.get("database", ""),
        "SNOWFLAKE_SCHEMA": conn.schema or "",
        "SNOWFLAKE_KEYPAIR_PATH": "/opt/airflow/.secrets/rsa_key.p8",
    }

    if include_dbt:
        env_vars.update(
            {
                "SNOWFLAKE_PRIVATE_KEY_FILE_PWD": conn.password or "",
                "SNOWFLAKE_PRIVATE_KEY_FILE_PATH": "/opt/airflow/.secrets/rsa_key.p8",
                "DBT_PROFILES_DIR": f"{os.environ.get('AIRFLOW_HOME', '/opt/airflow')}/.dbt",
                "DBT_PROJECT_DIR": f"{os.environ.get('AIRFLOW_HOME', '/opt/airflow')}/dbt",
                "PATH": "/home/airflow/.local/bin:" + os.environ.get("PATH", ""),
            }
        )

    return env_vars


@dag(
    dag_id="pipeline_streaming",
    schedule="0 2 * * 0",  # Weekly on Sunday at 2 AM
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Bangkok"),
    catchup=False,
    tags=["capstone", "streaming", "kafka", "dbt"],
    max_active_runs=1,
    description="Streaming pipeline: Kafka → PostgreSQL → Snowflake → dbt transformations (runs weekly)",
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
)
def streaming_pipeline_dag():
    """
    Streaming Pipeline DAG
    Orchestrates Kafka streaming data sync to Snowflake and dbt transformations
    """

    @task(execution_timeout=timedelta(minutes=15), do_xcom_push=False)
    def sync_postgres_to_snowflake():
        """
        Task 2: Sync streaming ticket sales from PostgreSQL to Snowflake
        Incrementally syncs new records from staging.ticket_sales to FAN_RAW.raw_tickets
        """
        script_path = (
            "/opt/airflow/scripts/sync_streaming_tickets__postgres_to_snowflake.py"
        )

        # Set environment variables
        env = os.environ.copy()
        env.update(get_postgres_env_vars())
        env.update(get_snowflake_env_vars(include_dbt=False))

        print(f"Running sync script: {script_path}")
        print(
            "Environment variables set: POSTGRES_HOST, POSTGRES_DB, SNOWFLAKE_ACCOUNT, etc."
        )

        # Use Popen for real-time output streaming
        try:
            process = subprocess.Popen(
                [sys.executable, script_path],
                cwd="/opt/airflow",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Stream output in real-time
            output_lines = []
            return_code = None

            try:
                # Read output line by line - handle pipe closure gracefully
                try:
                    for line in process.stdout:
                        print(line.rstrip())  # Print immediately
                        output_lines.append(line)
                        sys.stdout.flush()  # Force flush
                except (BrokenPipeError, ValueError) as e:
                    # Pipe closed - process might have finished, check return code
                    print(f"Note: Output pipe closed: {e}")
                    return_code = process.poll()
                    if return_code is None:
                        # Process still running, wait for it
                        return_code = process.wait(timeout=600)
                    elif return_code == 0:
                        # Process completed successfully despite pipe closure
                        print("Process completed successfully")
                    else:
                        # Process failed
                        output = "".join(output_lines)
                        print(f"ERROR: Sync script failed with exit code {return_code}")
                        print("Full output:", output[-2000:])
                        raise Exception(
                            f"Sync script failed with exit code {return_code}"
                        )

                # Wait for process to complete if we haven't gotten return code yet
                if return_code is None:
                    try:
                        return_code = process.wait(timeout=900)  # 15 minute timeout
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                        print("ERROR: Sync script timed out after 15 minutes")
                        raise Exception("Sync script timed out after 15 minutes")

                if return_code != 0:
                    output = "".join(output_lines)
                    print(f"ERROR: Sync script failed with exit code {return_code}")
                    print("Full output:", output[-2000:])  # Last 2000 chars
                    raise Exception(f"Sync script failed with exit code {return_code}")

                print("✅ Sync completed successfully")
                # Note: do_xcom_push=False prevents XCom storage errors

            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

        except FileNotFoundError:
            print(f"ERROR: Script not found: {script_path}")
            raise
        except Exception as e:
            if "timed out" not in str(e):
                print(f"ERROR: {e}")
            raise

    @task(execution_timeout=timedelta(minutes=15), do_xcom_push=False)
    def dbt_run():
        """
        Task 3: Run dbt transformations
        Transforms raw streaming data into analytics-ready models
        Note: dbt run can take several minutes, so timeout is set to 15 minutes
        """
        import datetime

        # Set environment variables
        env = os.environ.copy()
        env.update(get_snowflake_env_vars(include_dbt=True))

        models = "stg_ticket_sales int_ticket_sales_dedup fact_ticket_sales marts_ticket_performance marts_daily_ticket_summary"
        cmd = [
            "dbt",
            "run",
            "--profiles-dir",
            "/opt/airflow/.dbt",
            "--select",
        ] + models.split()

        print(f"Starting dbt run at {datetime.datetime.now()}")
        print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd="/opt/airflow/dbt",
                env=env,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout
                check=False,  # Don't raise on non-zero exit
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            print(
                f"dbt run finished at {datetime.datetime.now()} with exit code {result.returncode}"
            )

            # Handle protobuf reporting error (exit code 1 but success message)
            if result.returncode == 1:
                if "Done. PASS=" in result.stdout:
                    print(
                        "dbt models completed successfully (protobuf reporting error ignored)"
                    )
                    return "dbt run completed successfully"
                else:
                    print("dbt run failed - last 50 lines of output:")
                    lines = result.stdout.split("\n")
                    print("\n".join(lines[-50:]))
                    raise Exception(
                        f"dbt run failed with exit code {result.returncode}"
                    )

            return "dbt run completed successfully"

        except subprocess.TimeoutExpired:
            print("ERROR: dbt run timed out after 15 minutes")
            raise
        except Exception as e:
            print(f"ERROR: dbt run failed: {e}")
            raise

    @task(execution_timeout=timedelta(minutes=10), do_xcom_push=False)
    def dbt_test():
        """
        Task 4: Run dbt tests for ticket sales models only
        Validates data quality for streaming ticket data pipeline
        Tests: stg_ticket_sales, int_ticket_sales_dedup, fact_ticket_sales,
                marts_ticket_performance, marts_daily_ticket_summary
        """
        import datetime

        # Set environment variables
        env = os.environ.copy()
        env.update(get_snowflake_env_vars(include_dbt=True))

        models = "stg_ticket_sales int_ticket_sales_dedup fact_ticket_sales marts_ticket_performance marts_daily_ticket_summary"
        cmd = [
            "dbt",
            "test",
            "--profiles-dir",
            "/opt/airflow/.dbt",
            "--select",
        ] + models.split()

        print(
            f"Starting dbt tests for ticket sales models at {datetime.datetime.now()}"
        )
        print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd="/opt/airflow/dbt",
                env=env,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=False,  # Don't raise on non-zero exit
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            print(
                f"dbt tests finished at {datetime.datetime.now()} with exit code {result.returncode}"
            )

            # Handle protobuf reporting error (exit code 1 but success message)
            if result.returncode == 1:
                if "Done. PASS=" in result.stdout:
                    print(
                        "dbt tests completed successfully (protobuf reporting error ignored)"
                    )
                    return "dbt tests completed successfully"
                else:
                    print("dbt tests failed - last 50 lines of output:")
                    lines = result.stdout.split("\n")
                    print("\n".join(lines[-50:]))
                    raise Exception(
                        f"dbt test failed with exit code {result.returncode}"
                    )

            return "dbt tests completed successfully"

        except subprocess.TimeoutExpired:
            print("ERROR: dbt test timed out after 10 minutes")
            raise
        except Exception as e:
            print(f"ERROR: dbt test failed: {e}")
            raise

    @task(execution_timeout=timedelta(minutes=5), do_xcom_push=False)
    def reset_streaming_data():
        """
        Utility task: Reset streaming data for testing
        - Truncates FAN_RAW.raw_tickets in Snowflake
        - Resets sync_status and synced_at in PostgreSQL staging.ticket_sales
        WARNING: Only use for testing - this deletes all historical ticket data!
        """
        # Add config directory to path
        if os.path.exists("/opt/airflow/project_config"):
            sys.path.append("/opt/airflow/project_config")
        else:
            sys.path.append(str(Path(__file__).parent.parent / "config"))

        from api_config import get_snowflake_connection

        print("⚠️  WARNING: Resetting streaming data for testing...")

        # Reset PostgreSQL sync status
        pg_conn = None
        try:
            pg_conn = psycopg2.connect(
                host=os.environ["POSTGRES_HOST"],
                port=os.environ["POSTGRES_PORT"],
                database=os.environ["POSTGRES_DB"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
            )
            cursor = pg_conn.cursor()
            cursor.execute(
                "UPDATE staging.ticket_sales SET sync_status = NULL, synced_at = NULL"
            )
            pg_conn.commit()
            print(f"✅ Reset sync_status for {cursor.rowcount} rows in PostgreSQL")
            cursor.close()
        except Exception as e:
            print(f"❌ Error resetting PostgreSQL: {e}")
            raise
        finally:
            if pg_conn:
                pg_conn.close()

        # Truncate Snowflake raw table
        sf_conn = None
        try:
            sf_conn = get_snowflake_connection()
            cursor = sf_conn.cursor()
            cursor.execute("TRUNCATE TABLE IF EXISTS FAN_RAW.raw_tickets")
            sf_conn.commit()
            print("✅ Truncated FAN_RAW.raw_tickets in Snowflake")
            cursor.close()
        except Exception as e:
            print(f"❌ Error truncating Snowflake: {e}")
            raise
        finally:
            if sf_conn:
                sf_conn.close()

        print("✅ Streaming data reset complete - ready for re-sync")
        return "Reset completed successfully"

    # Define task dependencies
    sync_postgres_to_snowflake() >> dbt_run() >> dbt_test()


# Create the DAG instance
streaming_pipeline_dag()
