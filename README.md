# Data Engineering Capstone Project

## Overview
- **Working title**: FANalyze 2.0
- **One-sentence summary**:
    FANalyze is an end-to-end data engineering and AI analytics platform that integrates
    real-time concert setlist data, historical sources, and (in progress) ticket sales to
    uncover trends in artist performance, audience engagement, and cultural impact.
- **Business/value objective**:
    FANalyze delivers insights into music performance and fan demand by combining setlists,
    historical data, and ticket sales, helping artists and promoters make smarter touring
    and engagement decisions.
- **Success metrics** (quantitative):
    ⚡ Pipeline Latency: Real-time API events land in PostgreSQL and flow to Snowflake within <5 minutes
    🗄️ Data Completeness: Transformed warehouse tables maintain ≥95% schema-conformant records across all sources
    🔄 Data Diversity: At least 2 distinct data sources integrated (setlists + ticket sales)
    🤖 AI Agent Accuracy: RAG chatbot correctly answers ≥90% of benchmark queries about artist performance and ticket demand
    ✅ Test Coverage: Minimum 3 dbt tests per model layer (staging, intermediate, marts)

### Problem & Scope
- **Problem statement and constraints**:
    Fans and promoters lack a unified view of live music performance trends. While setlist
    data gives a record of what bands play, it does not tie into fan demand signals like
    ticket sales. Constraints include using publicly available APIs, managing API rate limits,
    and working with a mix of real-time and batch data.

- **Personas/stakeholders and primary use cases**:
    Fans → search historical setlists and see real-time updates from ongoing shows.
    Promoters/venues → analyze demand signals (ticket sales + attendance) to forecast interest.
    Artists/labels → compare setlist evolution across tours and cities.

- **In/out of scope**:
    In scope:
        Collecting setlist data (batch), 
        Loading and cleaning ticket sales data (real-time)
        Integrating into a warehouse, dbt modeling, RAG chatbot with document/PDF support.
    Out of scope:
        Real ticket sales data (often behind a paywall, or proprietary information)

### Data Sources
- **Real-time source**:
    Dataset: Synthetic ticket sales stream
    Format: JSON events (event_id, artist, venue, tickets_sold, timestamp, revenue, price_tier, etc.)
    Update frequency: Per second/minute events generated via Kafka producer
    Pipeline: Ticket sales events → Kafka → PostgreSQL (staging) → Snowflake
- **Batch source**: 
    Dataset: Concerts and setlists (exported JSON files from setlist.fm )
    Format: JSON (~5,000+ records: show_id, artist, venue, city, date, songs_played, etc.)
    Update cadence: Weekly updates loaded into Snowflake via Airflow
- **Why 2 different sources**:
    Ticket sales data provides a real-time demand signal, while concerts and setlists deliver historical performance context. 
    Together, they enable both operational monitoring (today’s ticket sales) and strategic insights (how setlists evolve across tours and cities).

### Architecture Overview
- **High-level diagram**: [ Link forthcoming as diagram is completed ]
    [Ticket Sales Events → Kafka → PostgreSQL → Airflow → Snowflake]
    [Concerts/Setlists CSVs → Airflow → Snowflake]
    Snowflake (dbt models) → LangGraph AI Agent (RAG) + Document Store

- **Data flow**: 
    1. Real-time: Ticket sales events stream into Kafka → PostgreSQL → Snowflake.
    2. Batch: Concert/setlist CSVs ingested in bulk into Snowflake via Airflow.
    3. Transformations: dbt builds clean staging, intermediate, and marts models.
    4. AI Agent: LangGraph chatbot queries Snowflake + documents via RAG.

- **Technology choices**:
    Kafka: ticket sales streaming ingestion.
    PostgreSQL: local OLTP staging DB for real-time loads.
    Snowflake: OLAP warehouse for unified analytics.
    dbt: modeling, testing, documentation.
    Airflow: orchestrates batch + real-time jobs.
    LangGraph + OpenAI/Claude: chatbot with conversation memory and RAG.
    GitHub Actions: CI/CD automation and testing.

## Project Structure
project/
├── .env                          # Configuration file
├── .gitignore                    # Git ignore file
├── main.py                       # Main pipeline script
├── scripts/
│   └── data_collection/         # Data collection scripts
├── data/
│   └── external/                 # Raw data files
└── pyproject.toml               # UV project configuration
## Setup
1. Install dependencies: `uv sync`
2. Configure environment: Copy `env_example.txt` to `.env`
3. Run pipeline: `uv run python main.py`

## Data Sources
- 
