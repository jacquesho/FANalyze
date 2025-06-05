from airflow.hooks.base import BaseHook
import snowflake.connector


def upload_setlists_to_stage():
    conn = BaseHook.get_connection("SF_JHo_connection")

    sf_conn = snowflake.connector.connect(
        user=conn.login,
        password=conn.password,
        account=conn.extra_dejson.get("account"),
        warehouse=conn.extra_dejson.get("warehouse"),
        database=conn.schema.split(".")[0] if "." in conn.schema else conn.schema,
        schema=conn.schema.split(".")[1] if "." in conn.schema else "FANALYZE",
        role=conn.extra_dejson.get("role"),
    )

    cursor = sf_conn.cursor()
    try:
        cursor.execute(
            "CREATE OR REPLACE STAGE DB_FANALYZE.FANALYZE.RAW_SETLISTS_STAGE"
        )
        cursor.execute("""
            PUT file:///opt/airflow/models/01_staging/setlistfm_data/all_band_setlists.json
            @DB_FANALYZE.FANALYZE.RAW_SETLISTS_STAGE AUTO_COMPRESS=FALSE
        """)
    finally:
        cursor.close()
        sf_conn.close()
