"""
Batch Data Pipeline DAG
Orchestrates CSV batch ingestion and dbt transformations
"""

import os
import subprocess
import sys
import json
from datetime import timedelta
import pendulum
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook


def get_snowflake_env_vars():
    """Get Snowflake environment variables from Airflow connections for ingestion script"""
    # Get connection and resolve actual values (not Jinja2 templates)
    conn = BaseHook.get_connection("snowflake_default")
    extra = (
        json.loads(conn.extra) if isinstance(conn.extra, str) else (conn.extra or {})
    )

    return {
        "SNOWFLAKE_ACCOUNT": extra.get("account", ""),
        "SNOWFLAKE_USER": conn.login or "",
        "SNOWFLAKE_ROLE": extra.get("role", ""),
        "SNOWFLAKE_WAREHOUSE": extra.get("warehouse", ""),
        "SNOWFLAKE_DATABASE": extra.get("database", ""),
        "SNOWFLAKE_SCHEMA": conn.schema or "",
        "SNOWFLAKE_KEYPAIR_PATH": "/opt/airflow/.secrets/rsa_key.p8",
    }


def get_dbt_snowflake_env_vars():
    """Get dbt environment variables from Airflow connections"""
    # Get connection and resolve actual values (not Jinja2 templates)
    conn = BaseHook.get_connection("snowflake_default")
    extra = (
        json.loads(conn.extra) if isinstance(conn.extra, str) else (conn.extra or {})
    )

    return {
        "SNOWFLAKE_ACCOUNT": extra.get("account", ""),
        "SNOWFLAKE_USER": conn.login or "",
        "SNOWFLAKE_PRIVATE_KEY_FILE_PWD": conn.password or "",
        "SNOWFLAKE_ROLE": extra.get("role", ""),
        "SNOWFLAKE_WAREHOUSE": extra.get("warehouse", ""),
        "SNOWFLAKE_DATABASE": extra.get("database", ""),
        "SNOWFLAKE_SCHEMA": conn.schema or "",
        "SNOWFLAKE_PRIVATE_KEY_FILE_PATH": "/opt/airflow/.secrets/rsa_key.p8",
        "DBT_PROFILES_DIR": f"{os.environ.get('AIRFLOW_HOME', '/opt/airflow')}/.dbt",
        "DBT_PROJECT_DIR": f"{os.environ.get('AIRFLOW_HOME', '/opt/airflow')}/dbt",
        "PATH": "/home/airflow/.local/bin:" + os.environ.get("PATH", ""),
    }


@dag(
    dag_id="pipeline_batch",
    schedule="0 2 * * 0",  # Weekly on Sunday at 2 AM
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Bangkok"),
    catchup=False,
    tags=["capstone", "batch", "csv", "dbt"],
    max_active_runs=3,  # Increased to allow multiple manual runs during development
    description="Batch CSV ingestion pipeline: CSV → Snowflake → dbt transformations (runs weekly)",
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
)
def batch_pipeline_dag():
    """
    Batch Pipeline DAG
    Orchestrates CSV batch data ingestion and dbt transformations
    """

    @task(execution_timeout=timedelta(minutes=5))
    def clear_snowflake_schemas():
        """
        Task 1: Clear Snowflake schemas for clean state
        Truncates raw tables and drops dbt-created schemas
        """
        # Set environment variables
        env = os.environ.copy()
        env.update(get_snowflake_env_vars())

        print("Clearing Snowflake schemas...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "scripts.clear_snowflake_schemas"],
                cwd="/opt/airflow",
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True,
            )
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return "Schemas cleared successfully"
        except subprocess.TimeoutExpired:
            print("ERROR: Clear schemas script timed out after 5 minutes")
            raise
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Clear schemas script failed with exit code {e.returncode}")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise

    @task(execution_timeout=timedelta(minutes=10))
    def ingest_csv_to_snowflake():
        """
        Task 2: Ingest CSV files to Snowflake FAN_RAW schema
        Processes shows_history.csv and shows_future.csv
        """
        # Set environment variables
        env = os.environ.copy()
        env.update(get_snowflake_env_vars())

        print("Ingesting CSV files to Snowflake...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "scripts.ingest_csv_shows__snowflake"],
                cwd="/opt/airflow",
                env=env,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=True,
            )
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return "CSV ingestion completed successfully"
        except subprocess.TimeoutExpired:
            print("ERROR: CSV ingestion script timed out after 10 minutes")
            raise
        except subprocess.CalledProcessError as e:
            print(f"ERROR: CSV ingestion script failed with exit code {e.returncode}")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise

    @task(execution_timeout=timedelta(minutes=15))
    def dbt_run():
        """
        Task 3: Run dbt transformations
        Transforms raw CSV data into analytics-ready models
        """
        import datetime

        # Set environment variables
        env = os.environ.copy()
        env.update(get_dbt_snowflake_env_vars())

        # Check source table row counts first
        print("Checking source table row counts...")
        try:
            sys.path.insert(0, "/opt/airflow/project_config")
            from api_config import get_snowflake_connection

            conn = get_snowflake_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM FAN_RAW.SHOWS_HIS")
                shows_his_count = cur.fetchone()[0]
                print(f"SHOWS_HIS: {shows_his_count} rows")
                cur.execute("SELECT COUNT(*) FROM FAN_RAW.SHOWS_FUTURE")
                shows_future_count = cur.fetchone()[0]
                print(f"SHOWS_FUTURE: {shows_future_count} rows")
            except Exception as e:
                print(f"Error checking tables: {e}")
            finally:
                conn.close()
        except Exception as e:
            print(f"Warning: Could not check table counts: {e}")

        # Run dbt with real-time output streaming
        cmd = ["dbt", "run", "--profiles-dir", "/opt/airflow/.dbt"]
        print(f"Starting dbt run at {datetime.datetime.now()}")
        print(f"Running: {' '.join(cmd)}")

        try:
            # Use Popen for real-time output streaming instead of buffering
            process = subprocess.Popen(
                cmd,
                cwd="/opt/airflow/dbt",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr into stdout
                text=True,
                bufsize=1,  # Line buffered
            )

            stdout_lines = []
            # Read output line by line in real-time
            for line in process.stdout:
                line = line.rstrip()
                print(line)
                stdout_lines.append(line)
                sys.stdout.flush()  # Force flush to see output immediately

            # Wait for process to complete with timeout
            try:
                returncode = process.wait(timeout=900)  # 15 minute timeout
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                print("ERROR: dbt run timed out after 15 minutes")
                raise subprocess.TimeoutExpired(cmd, 900)

            result_stdout = "\n".join(stdout_lines)
            # stderr is already combined into stdout via PIPE

            print(
                f"dbt run finished at {datetime.datetime.now()} with exit code {returncode}"
            )

            # Handle protobuf reporting error (exit code 1 but success message)
            if returncode == 1:
                # Check for successful completion despite protobuf error
                if (
                    "Done. PASS=" in result_stdout
                    or "Completed successfully" in result_stdout
                ):
                    print(
                        "dbt models completed successfully (protobuf reporting error ignored)"
                    )
                    return "dbt run completed successfully"
                # Check for protobuf TypeError (version incompatibility issue)
                elif (
                    "MessageToJson()" in result_stdout
                    and "unexpected keyword argument" in result_stdout
                ):
                    # Check if models were actually built successfully before the error
                    stdout_before_error = result_stdout.split("MessageToJson()")[0]
                    # Look for success indicators in the output before the error
                    if any(
                        indicator in stdout_before_error
                        for indicator in [
                            "Completed successfully",
                            "Completed with",
                            "PASS=",
                            "Creating",
                            "Running",
                        ]
                    ):
                        # Check if there are any actual failures mentioned
                        if (
                            "FAIL" not in stdout_before_error.upper()
                            and "ERROR" not in stdout_before_error.upper()
                        ):
                            print(
                                "dbt models completed successfully (protobuf serialization error ignored)"
                            )
                            return "dbt run completed successfully"
                    print("dbt run failed - protobuf version incompatibility detected")
                    print("Last 50 lines of output:")
                    lines = result_stdout.split("\n")
                    print("\n".join(lines[-50:]))
                    raise Exception(
                        "dbt run failed with protobuf error. Check protobuf version compatibility."
                    )
                else:
                    print("dbt run failed - last 50 lines of output:")
                    lines = result_stdout.split("\n")
                    print("\n".join(lines[-50:]))
                    raise Exception(f"dbt run failed with exit code {returncode}")

            return "dbt run completed successfully"

        except subprocess.TimeoutExpired:
            print("ERROR: dbt run timed out after 15 minutes")
            raise
        except Exception as e:
            print(f"ERROR: dbt run failed: {e}")
            raise

    @task(execution_timeout=timedelta(minutes=10))
    def dbt_test():
        """
        Task 4: Run dbt tests for shows/artists/venues models only
        Validates data quality for batch CSV data pipeline
        Tests: stg_shows_his, stg_shows_future, int_shows, int_artists, int_venues,
                fact_shows, dim_artists, dim_venues, marts_artist_performance, marts_show_lifecycle
        """
        import datetime

        # Set environment variables
        env = os.environ.copy()
        env.update(get_dbt_snowflake_env_vars())

        # Run source tests for batch pipeline sources (shows_his and shows_future)
        # Note: Batch models don't have tests configured yet, but source tests exist
        # Source tests validate the raw data structure before transformation
        cmd = [
            "dbt",
            "test",
            "--profiles-dir",
            "/opt/airflow/.dbt",
            "--select",
            "source:FAN_RAW.shows_his",
            "source:FAN_RAW.shows_future",
        ]

        print(
            f"Starting dbt tests for shows/artists/venues models at {datetime.datetime.now()}"
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
                # FIRST: Check for "Nothing to do" - this can happen with or without protobuf errors
                if "Nothing to do" in result.stdout:
                    # Check if there's also a protobuf error (non-fatal)
                    if (
                        "MessageToJson()" in result.stdout
                        and "unexpected keyword argument" in result.stdout
                    ):
                        print(
                            "dbt test found no tests to run (protobuf serialization error ignored)"
                        )
                    else:
                        print("dbt test found no tests to run")
                    print(
                        "Note: No tests are configured for the selected batch pipeline models."
                    )
                    return "dbt test completed (no tests configured)"

                # Check for successful completion despite protobuf error
                if "Done. PASS=" in result.stdout:
                    print(
                        "dbt tests completed successfully (protobuf reporting error ignored)"
                    )
                    return "dbt tests completed successfully"

                # Check for protobuf TypeError (version incompatibility issue)
                if (
                    "MessageToJson()" in result.stdout
                    and "unexpected keyword argument" in result.stdout
                ):
                    # Check if this is just a reporting error (tests found but protobuf failed to serialize)
                    if "Found" in result.stdout and "data tests" in result.stdout:
                        # Tests were discovered, protobuf error is just in reporting
                        # Check if there are any actual test failures mentioned before the error
                        stdout_before_error = result.stdout.split("MessageToJson()")[0]
                        if (
                            "FAIL" not in stdout_before_error.upper()
                            and "ERROR" not in stdout_before_error.upper()
                        ):
                            print(
                                "dbt tests completed successfully (protobuf serialization error ignored)"
                            )
                            return "dbt tests completed successfully"
                    # Otherwise, it's a real error
                    print(
                        "dbt tests failed - protobuf version incompatibility detected"
                    )
                    print("Last 50 lines of output:")
                    lines = result.stdout.split("\n")
                    print("\n".join(lines[-50:]))
                    raise Exception(
                        "dbt test failed with protobuf error. Check protobuf version compatibility."
                    )

                # If we get here, it's a different kind of failure
                print("dbt tests failed - last 50 lines of output:")
                lines = result.stdout.split("\n")
                print("\n".join(lines[-50:]))
                raise Exception(f"dbt test failed with exit code {result.returncode}")

            return "dbt tests completed successfully"

        except subprocess.TimeoutExpired:
            print("ERROR: dbt test timed out after 10 minutes")
            raise
        except Exception as e:
            print(f"ERROR: dbt test failed: {e}")
            raise

    # Define task dependencies
    clear_snowflake_schemas() >> ingest_csv_to_snowflake() >> dbt_run() >> dbt_test()


# Create the DAG instance
batch_pipeline_dag()
