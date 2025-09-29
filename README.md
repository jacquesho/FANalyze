# Data Engineering Capstone Project

## Overview
- **Working title**: FANalyze 2.0
- **One-sentence summary**:
FANalyze is an end-to-end data engineering and AI analytics platform that integrates real-time concert setlist data, historical sources, and (in progress) ticket sales to uncover trends in artist performance, audience engagement, and cultural impact.
- **Business/value objective**:
FANalyze delivers insights into music performance and fan demand by combining setlists, historical data, and ticket sales, helping artists and promoters make smarter touring and engagement decisions.
- **Success metrics** (quantitative):
⚡ Pipeline Latency: Real-time API events land in PostgreSQL and flow to Snowflake within <5 minutes
🗄️ Data Completeness: Transformed warehouse tables maintain ≥95% schema-conformant records across all sources
🔄 Data Diversity: At least 2 distinct data sources integrated (setlists + ticket sales)
🤖 AI Agent Accuracy: RAG chatbot correctly answers ≥90% of benchmark queries about artist performance and ticket demand
✅ Test Coverage: Minimum 3 dbt tests per model layer (staging, intermediate, marts)


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
- [List your chosen data sources here]