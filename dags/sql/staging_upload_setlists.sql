# upload_setlists_to_stage.py

import os
import snowflake.connector
from airflow.models import Variable

def upload_setlists_to_stage():
    # Credentials from Airflow Connections (or you can hardcode for now)
    conn = snowflake.connector.connect(
        user=os.getenv("SF_USER"),
        password=os.getenv("SF_PASSWORD"),
        account=os.getenv("SF_ACCOUNT"),
        warehouse="WH_FANALYZE",
        database="DB_FANALYZE",
        schema="STAGING",
        role="ROLE_FANALYZE"
    )

    cursor = conn.cursor()
    try:
        cursor.execute("CREATE OR REPLACE STAGE DB_FANALYZE.STAGING.STAGING_SETLISTS_STAGE")
        cursor.execute("""
            PUT file:///opt/airflow/models/01_staging/setlistfm_data/all_band_setlists.json
            @DB_FANALYZE.STAGING.STAGING_SETLISTS_STAGE AUTO_COMPRESS=FALSE
        """)
    finally:
        cursor.close()
        conn.close()
