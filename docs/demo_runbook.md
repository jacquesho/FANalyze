# Demo runbook (end-to-end)

This runbook keeps the repo **runnable** while avoiding committed secrets. Copy `.env.example` to `.env` and fill in values before running anything.

## 0) One-time setup

### Create the shared Docker network

```bash
docker network create fa-dae2-capstone_kafka_network
```

### Configure environment variables

```bash
# macOS / Linux / Git Bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## 1) Start Postgres (staging)

```bash
docker compose -f docker-compose.yaml up -d kafka-postgres
```

## 2) Streaming pipeline (Kafka → Postgres)

### Start Kafka (and optional UI)

```bash
docker compose -f docker-compose-kafka.yml up -d kafka
# Optional Kafka UI:
docker compose -f docker-compose-kafka.yml --profile ui up -d
```

### Run producer + consumer (local dev, easiest)

In two terminals:

```bash
uv sync
uv run python kafka/consumers/postgres_consumer.py
```

```bash
uv run python kafka/producers/ticket_producer.py
```

### Or run producer + consumer in Docker (more “demo-like”)

```bash
docker compose -f docker-compose-kafka.yml --profile app up -d --build
docker compose -f docker-compose-kafka.yml logs -f ticket-producer postgres-consumer
```

## 3) Sync Postgres → Snowflake (streaming)

```bash
uv run python scripts/sync_tickets__postgres_to_snowflake.py
```

## 4) Batch pipeline (Setlist.fm → Snowflake → dbt)

```bash
uv run python scripts/export_setlistfm_history_to_csv.py
uv run python scripts/generate_future_concerts.py
uv run python scripts/ingest_csv_shows__snowflake.py
```

Run dbt models/tests:

```bash
uv run dbt deps --project-dir dbt
uv run dbt run --project-dir dbt
uv run dbt test --project-dir dbt
```

## 5) Streamlit apps

### RAG / LangGraph app

```bash
uv run streamlit run langgraph/streamlit_app.py
```

### Main Streamlit app (if used)

```bash
uv run streamlit run streamlit_app.py
```

## 6) Airflow (optional orchestration)

```bash
docker compose -f docker-compose-airflow.yml up -d --build
```

Airflow UI: `http://localhost:8080` (default login: `airflow` / `airflow`).

