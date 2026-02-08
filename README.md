# FANalyze 2.0 🎵📊

> **A comprehensive data engineering and AI analytics platform for music industry insights**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.4-blue.svg)](https://postgresql.org)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-orange.svg)](https://snowflake.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Project Overview

**FANalyze 2.0** is an end-to-end data engineering and AI analytics platform that integrates concert setlist data, historical sources, and real-time ticket sales to uncover trends in artist performance, audience engagement, and cultural impact.

### 🚀 Key Features
- **Real-time Data Pipeline**: Live ticket sales streaming with Kafka → PostgreSQL → Snowflake
- **Batch Data Processing**: Historical setlist data with dbt transformations
- **AI-Powered Analytics**: LangGraph chatbot with RAG for natural language queries
- **Comprehensive Monitoring**: Full observability with performance metrics and alerts

### 💼 Business Value
FANalyze delivers actionable insights into music performance and fan demand by combining setlists, historical data, and ticket sales, helping artists and promoters make smarter touring and engagement decisions.

### 📊 Success Metrics
- ⚡ **Pipeline Latency**: Real-time events land in PostgreSQL and flow to Snowflake within <5 minutes
- 🔄 **Data Diversity**: At least 2 distinct data sources integrated (setlists + ticket sales)
- 🤖 **AI Agent Accuracy**: RAG chatbot correctly answers ≥90% of benchmark queries
- ✅ **Test Coverage**: Minimum 3 dbt tests per model layer (staging, intermediate, marts)

## 🎭 Problem & Scope

### Problem Statement
Fans and promoters lack a unified view of live music performance trends. While setlist data provides a record of what bands play, it doesn't connect to fan demand signals like ticket sales, creating a fragmented understanding of the music industry.

### Key Constraints
- Using publicly available APIs with rate limits
- Working with synthetic data (real ticket sales data is proprietary)
- Managing data quality across multiple sources
- Ensuring real-time processing capabilities

### 👥 Target Users
- **🎵 Fans**: Search historical setlists and see real-time updates from ongoing shows
- **🏟️ Promoters/Venues**: Analyze demand signals (ticket sales + attendance) to forecast interest
- **🎤 Artists/Labels**: Compare setlist evolution across tours and cities

### 📋 Scope Definition
**✅ In Scope:**
- Collecting setlist data (batch processing)
- Loading and cleaning ticket sales data (real-time)
- Data warehouse integration with dbt modeling
- RAG chatbot with document/PDF support
- Performance monitoring and alerting

**❌ Out of Scope:**
- Real ticket sales data (proprietary/paywall protected)
- Social media sentiment analysis
- Financial transaction processing

## 📊 Data Sources

### 🔴 Real-time Source: Synthetic Ticket Sales
- **Dataset**: Synthetic ticket sales stream
- **Format**: JSON events with fields: `event_id`, `artist`, `venue`, `tickets_sold`, `timestamp`, `revenue`, `price_tier`
- **Update Frequency**: Per second/minute events generated via Kafka producer
- **Pipeline**: Ticket sales events → Kafka → PostgreSQL (staging) → Snowflake
- **Volume**: 100+ events per minute during peak hours

### 🔵 Batch Source: Concert Setlists
- **Dataset**: Concerts and setlists from setlist.fm
- **Format**: JSON files (~5,000+ records per artist)
- **Fields**: `show_id`, `artist`, `venue`, `city`, `date`, `songs_played`, `tour_name`
- **Update Cadence**: Weekly bulk loads into Snowflake via Airflow
- **Volume**: 500+ records per batch load

### 🔄 Why Two Different Sources?
Ticket sales data provides **real-time demand signals**, while setlists deliver **historical performance context**. Together, they enable:
- **Operational Monitoring**: Today's ticket sales and demand patterns
- **Strategic Insights**: How setlists evolve across tours and cities
- **Predictive Analytics**: Forecasting demand based on historical patterns

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Real-time     │    │    Kafka     │     │ PostgreSQL  │     │  Snowflake  │
│ Ticket Sales    │───▶│   Streaming  │───▶│  Staging    │───▶│  Warehouse  │
│   (Synthetic)   │    │              │     │             │     │             │
└─────────────────┘    └──────────────┘     └─────────────┘     └─────────────┘
                                                      ▲
┌─────────────────┐     ┌──────────────┐              │
│   Batch Data    │     │   Airflow    │──────────────┘
│   (Setlists)    │───▶│ Orchestrator │
└─────────────────┘     └──────────────┘
                                │
                                ▼
┌─────────────────┐     ┌─────────────--─┐    ┌─────────────┐
│   AI Agent      │◀───│    dbt         │◀───│  Snowflake  │
│  (LangGraph)    │     │ Transformations│    │  Warehouse  │
└─────────────────┘     └─────────────--─┘    └─────────────┘
```

### 🔄 Data Flow
1. **Real-time Pipeline**: Ticket sales events → Kafka → PostgreSQL → Snowflake
2. **Batch Pipeline**: Concert/setlist data → Airflow → Snowflake
3. **Data Transformation**: dbt builds staging, intermediate, and marts models
4. **AI Integration**: LangGraph chatbot queries Snowflake + documents via RAG

### 🛠️ Technology Stack
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Streaming** | Kafka | Real-time ticket sales ingestion |
| **Staging DB** | PostgreSQL | Local OLTP for real-time loads |
| **Warehouse** | Snowflake | OLAP analytics and storage |
| **Transformations** | dbt | Data modeling, testing, documentation |
| **Orchestration** | Airflow | Batch and real-time job coordination |
| **AI Agent** | LangGraph + OpenAI/Claude | Conversational AI with RAG |
| **CI/CD** | GitHub Actions | Automation and testing |

## 📁 Project Structure
```
FANalyze_v2.0/
├── 📄 README.md                    # Project documentation
├── 📄 pyproject.toml              # UV project configuration
├── 📄 docker-compose.yaml         # Docker services configuration
├── 📄 .env.example                # Environment variables template
├── 📄 .gitignore                  # Git ignore patterns
├── 📁 config/                     # Configuration files
│   └── 📄 settings.py             # Application settings
├── 📁 docs/                       # Documentation
│   └── 📄 execution_plan.md       # Detailed implementation plan
├── 📁 scripts/                    # Data processing scripts
│   ├── 📁 data_collection/        # Data ingestion scripts
│   ├── 📁 database/              # Database operations
│   ├── 📁 monitoring/             # Performance monitoring
│   └── 📁 validation/             # Data quality checks
├── 📁 data/                       # Data storage
│   └── 📁 external/              # Raw data files
├── 📁 sql/                        # SQL scripts
│   └── 📄 init.sql               # Database initialization
├── 📁 tests/                      # Test suite
│   ├── 📄 test_connections.py    # Database connection tests
│   └── 📄 test_data_pipeline.py  # Pipeline validation tests
└── 📄 main.py                     # Main pipeline orchestrator
```
## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- UV package manager
- Snowflake account (for data warehouse)

### 1. 📦 Install Dependencies
```bash
# Install UV if not already installed
pip install uv

# Install project dependencies
uv sync --dev
```

### 2. ⚙️ Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values:
# - PostgreSQL credentials (for local staging)
# - Snowflake credentials (for data warehouse)
# - API keys (for data collection)
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 3. 🗄️ Initialize Databases
```bash
# Create the shared network (one-time)
docker network create fa-dae2-capstone_kafka_network

# Start PostgreSQL via Docker
docker compose -f docker-compose.yaml up -d kafka-postgres
```

### 4. 🔄 Run the demo

See the end-to-end runbook:

- [`docs/demo_runbook.md`](docs/demo_runbook.md)

### 5. ✅ Verify Data
```bash
# Run the DB test suite
uv run pytest tests/DB_tests -v
```

## 🧪 Testing

### Run All Tests
```bash
# Run complete test suite
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=scripts --cov-report=html
```

### Data quality checks (example)
```bash
uv run python scripts/validation/data_validation.py
```

## 🛠️ Development

### Code Quality
```bash
# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

### Database Management
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d postgres

# Connect to Snowflake
uv run python -c "
import snowflake.connector
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    private_key_file_path=os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE'),
    schema=os.getenv('SNOWFLAKE_SCHEMA')
)
"
```

## 🐛 Troubleshooting

### Common Issues
1. **PostgreSQL Connection**: Check Docker is running, credentials in .env
2. **Snowflake Connection**: Verify private key path and permissions
3. **Data Format**: Ensure JSON is valid, check file encoding
4. **Environment**: Run `uv run python -c "import os; print(os.getenv('POSTGRES_HOST'))"` to verify env loading

### Debug Commands
```bash
# Test connections
uv run pytest tests/test_connections.py -v

# Check environment
uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print([k for k in os.environ if 'POSTGRES' in k or 'SNOWFLAKE' in k])"

# Verify data files
ls -la data/external/
file data/external/*.json
```

## 📚 Documentation

- [Demo runbook](docs/demo_runbook.md) - End-to-end commands
- [Execution plan](docs/misc/execution_plan.md)
- [API notes](docs/misc/api.md)
- [Data model](docs/misc/data_model.md)
- [Deployment](docs/misc/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [setlist.fm](https://www.setlist.fm/) for providing setlist data
- [Foundry AI Academy](https://foundry-ai-academy.com/) for the educational framework
- The open-source community for the amazing tools and libraries
