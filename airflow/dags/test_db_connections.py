"""
FANalyze DB Connection Test DAG
Tests connections to PostgreSQL and Snowflake databases.
Use this DAG to verify that your Airflow connections are configured correctly.
"""

import logging

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
import pendulum


@dag(
    dag_id="test_db_connections",
    schedule=None,  # Manual trigger only
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["test", "db-connection", "integration"],
    max_active_runs=1,
    description="Test connections to PostgreSQL and Snowflake databases",
)
def test_db_connections():
    """
    ### FANalyze DB Connection Test DAG
    Tests connections to PostgreSQL (kafka-postgres) and Snowflake databases.
    Run this DAG manually to verify your connections are working correctly.
    """

    @task()
    def test_snowflake_connection():
        """
        #### Snowflake Connection Test
        Tests connection to Snowflake and validates basic functionality.
        Uses connection: snowflake_default
        """
        logger = logging.getLogger(__name__)
        logger.info("🔍 Testing Snowflake connection...")

        try:
            snowflake_hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
            conn = snowflake_hook.get_conn()
            cursor = conn.cursor()

            # Test basic connection
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]

            # Test database access
            cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
            db_info = cursor.fetchone()
            database, schema, warehouse = db_info

            logger.info(f"✅ Snowflake connection successful!")
            logger.info(f"   Version: {version}")
            logger.info(f"   Database: {database}")
            logger.info(f"   Schema: {schema}")
            logger.info(f"   Warehouse: {warehouse}")
            
            cursor.close()
            conn.close()

            return f"Connected to Snowflake - DB: {database}, Schema: {schema}, Warehouse: {warehouse}"
        except Exception as e:
            error_msg = f"Snowflake connection failed: {e}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg) from e

    @task()
    def test_postgres_connection():
        """
        #### PostgreSQL Connection Test
        Tests connection to PostgreSQL (kafka-postgres) and validates basic functionality.
        Uses connection: postgres_kafka_default
        """
        logger = logging.getLogger(__name__)
        logger.info("🔍 Testing PostgreSQL connection...")

        try:
            pg_hook = PostgresHook(postgres_conn_id="postgres_kafka_default")
            conn = pg_hook.get_conn()
            cursor = conn.cursor()

            # Test basic connection
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # Test database name
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            
            # Test schema access
            cursor.execute("SELECT current_schema()")
            schema = cursor.fetchone()[0]

            logger.info(f"✅ PostgreSQL connection successful!")
            logger.info(f"   Version: {version.split(',')[0]}")
            logger.info(f"   Database: {db_name}")
            logger.info(f"   Schema: {schema}")
            
            cursor.close()
            conn.close()
            
            return f"PostgreSQL connection verified - DB: {db_name}, Schema: {schema}"
        except Exception as e:
            error_msg = f"PostgreSQL connection failed: {e}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg) from e

    # Execute connection tests in parallel
    test_snowflake_connection()
    test_postgres_connection()

    # Both tasks run independently - no dependencies needed


# Create the DAG instance
test_db_connections()

