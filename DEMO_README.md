# FANalyze 2.0 Demo - Quick Commands

### 1. Fetch data via setlistfm API to generate shows_history.csv
```bash
uv run python scripts/export_setlistfm_history_to_csv.py

uv run python scripts/generate_future_concerts.py
```

### 2. Ingest both history + future to Snowflake
```bash
uv run python scripts/ingest_csv_shows__snowflake.py
```

### 3. Build dbt models
```bash
uv run dbt run
uv run dbt test
```

### 5. Stream ticket sales to Postgres (row-by-row)
```bash
uv run python scripts/stream_to_postgres.py
```

### 6. Sync Postgres → Snowflake
```bash
uv run python scripts/sync_streaming_tickets__postgres_to_snowflake.py
```

### 7. Incremental dbt update
```bash
uv run dbt run --select 01_staging.stg_ticket_sales+ 03_marts.fact_ticket_sales 03_marts.dim_ticket_performance 03_marts.fct_daily_ticket_summary
uv run dbt test
```
