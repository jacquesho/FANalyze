# FANalyze 2.0 Demo - Quick Commands

## Setup (one-time)
```bash
cd FANalyze_v2.0
docker-compose up -d
```

## Demo Run (copy-paste in order)

### 1. Ensure shows_history.csv exists (or fetch from Setlist.fm API)
```bash
# Skip if you already have data/raw/csv/shows_history.csv
# Otherwise fetch from API first

# Requires SETLISTFM_API_KEY in your environment
uv run python -c "from scripts.data_collection.setlistfm_api import SetlistFMAPI; api=SetlistFMAPI(); data=api.fetch_all_artists_historical(); api.save_data_to_file(data, 'setlistfm_full_history')"
```

### 2. Enrich history CSV with ticket sales data
```bash
uv run python scripts/enrich_history_from_setlistfm.py --input data/raw/csv/shows_history.csv --backup
```

### 3. Ingest both history + future to Snowflake
```bash
uv run python scripts/ingest_csv_shows__snowflake.py
```

### 4. Build dbt models
```bash
dbt run
dbt test
```

### 5. Stream ticket sales to Postgres (row-by-row)
```bash
uv run python scripts/stream_to_postgres.py --duration 1 --speed 5
```

### 6. Sync Postgres → Snowflake
```bash
uv run python scripts/sync_streaming_tickets__postgres_to_snowflake.py
```

### 7. Incremental dbt update
```bash
dbt run
dbt test
```
