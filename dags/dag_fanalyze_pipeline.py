import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from airflow.decorators import dag, task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

SHOWS_TABLE = "FANALYZE.PUBLIC.STAGING_SHOWS"
SETLISTS_TABLE = "FANALYZE.PUBLIC.STAGING_SETLISTS"

FACT_SQL_FILES = [
    "sql/insert_fact_shows.sql",
    "sql/insert_fact_setlists.sql",
    "sql/insert_fact_song_stats.sql",
    "sql/insert_fact_artists.sql",
]


def get_snowflake_hook():
    return SnowflakeHook(snowflake_conn_id="SF_JHo_connection")


@task
def find_show_csv() -> str:
    BASE    = Path(__file__).resolve().parent.parent
    STAGING = BASE / "01_staging" / "setlistfm_data"
    files   = list(STAGING.rglob("*.csv"))

    print("Found files in /opt/airflow/data:", [str(f) for f in files])
    csvs = [f for f in files if f.name.endswith(".csv")]
    if not csvs:
        raise FileNotFoundError("No CSV file found in {STAGING}")
    return str(csvs[0])


@task
def parse_and_batch_insert_shows(csv_path: str):
    print(f"Reading CSV from path: {csv_path}")
    df = pd.read_csv(csv_path)
    print("CSV Columns:", df.columns.tolist())
    print("First 3 rows of CSV:", df.head(3).to_dict(orient="records"))

    valid_rows = []
    for _, row in df.iterrows():
        try:
            parsed_date = pd.to_datetime(row.date, dayfirst=True).strftime("%Y-%m-%d")
            parsed_row = (
                row.artist_id,
                row.artist_name,
                parsed_date,
                row.setlist_id,
                row.venue,
                row.city,
                row.country,
                row.tour_name,
                row.ticket_tier,
                row.simulated_price_usd,
            )
            print("Parsed row:", parsed_row)
            valid_rows.append(parsed_row)
        except Exception as e:
            print(f"Skipping row due to error: {e}")

    print(f"Valid rows to insert: {len(valid_rows)}")

    if valid_rows:
        hook = get_snowflake_hook()
        insert_stmt = f"""
            INSERT INTO {SHOWS_TABLE} (
                ARTIST_ID, ARTIST_NAME, SHOW_DATE, SHOW_ID,
                VENUE, CITY, COUNTRY, TOUR_NAME,
                TICKET_TIER, SIMULATED_PRICE_USD
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            hook.get_conn().cursor().executemany(insert_stmt, valid_rows)
            print(f"✅ Successfully inserted {len(valid_rows)} rows into {SHOWS_TABLE}")
        except Exception as e:
            print(f"❌ Insert failed: {e}")
            raise


@task
def find_setlist_json() -> str:
    BASE    = Path(__file__).resolve().parent.parent
    STAGING = BASE / "01_staging" / "setlistfm_data"
    files   = list(STAGING.rglob("*.json"))

    print("Found files in /opt/airflow/data:", [str(f) for f in files])
    jsons = [f for f in files if f.name.endswith(".json")]
    if not jsons:
        raise FileNotFoundError("No JSON file found in {STAGING}")
    return str(jsons[0])


@task
def parse_and_batch_insert_setlists(json_path: str):
    print(f"Reading JSON from path: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Total records in JSON: {len(data)}")

    rows = []
    for entry in data:
        try:
            setlist_id = entry["id"]
            set_data = entry.get("sets", {}).get("set", [])
            if set_data:
                raw_json = json.dumps({"set": set_data}, ensure_ascii=False)
                rows.append((setlist_id, raw_json))
        except Exception as e:
            print(f"Skipping entry due to error: {e}")

    print(f"Valid rows to insert: {len(rows)}")

    if rows:
        hook = get_snowflake_hook()
        try:
            cursor = hook.get_conn().cursor()
            for row in rows:
                setlist_id, raw_json = row
                cursor.execute(
                    f"INSERT INTO {SETLISTS_TABLE} (SHOW_ID, SETLIST) SELECT %s, PARSE_JSON(%s)",
                    (setlist_id, raw_json),
                )
            print(f"✅ Successfully inserted {len(rows)} rows into {SETLISTS_TABLE}")
        except Exception as e:
            print(f"❌ Setlist insert failed: {e}")
            raise


@task
def run_fact_sql(sql_file: str):
    print(f"Running transformation SQL file: {sql_file}")
    hook = get_snowflake_hook()
    with open(sql_file, "r") as f:
        sql = f.read()
    try:
        hook.run(sql)
        print(f"✅ Successfully ran SQL: {sql_file}")
    except Exception as e:
        print(f"❌ Failed to run SQL {sql_file}: {e}")
        raise


@dag(
    dag_id="fanalyze_pipeline",
    schedule_interval=None,
    start_date=datetime(2025, 4, 1),
    catchup=False,
    tags=["fanalyze"],
)
def fanalyze_staging_pipeline():
    csv_path = find_show_csv()
    json_path = find_setlist_json()

    load_shows = parse_and_batch_insert_shows(csv_path)
    load_setlists = parse_and_batch_insert_setlists(json_path)

    transform_tasks = [
        run_fact_sql.override(task_id=f"run_{Path(sql).stem}")(sql)
        for sql in FACT_SQL_FILES
    ]

    # Chain the tasks using TaskFlow objects (not returned values)
    csv_path >> load_shows >> json_path >> load_setlists
    load_setlists >> transform_tasks


fanalyze_staging_pipeline()
