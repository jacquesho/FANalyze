# Troubleshooting LangGraph PostgreSQL Connection

## Issue
Streamlit shows "PostgreSQL not available - using in-memory storage"

## Required Environment Variables
The agent needs these variables in your `.env` file:
```
LANGGRAPH_POSTGRES_HOST=localhost  # or kafka-postgres if using Docker network
LANGGRAPH_POSTGRES_PORT=5432      # or 5433 if using langgraph-postgres-1
LANGGRAPH_POSTGRES_DB=langgraph_memory
LANGGRAPH_POSTGRES_USER=langgraph_service
LANGGRAPH_POSTGRES_PASSWORD=langgraph_service_password
```

## Step-by-Step Fix

### Option 1: Use Existing kafka-postgres-1 (Recommended)
Since `kafka-postgres-1` is already running on port 5432:

1. **Add to your `.env` file:**
   ```bash
   LANGGRAPH_POSTGRES_HOST=localhost
   LANGGRAPH_POSTGRES_PORT=5432
   LANGGRAPH_POSTGRES_DB=langgraph_memory
   LANGGRAPH_POSTGRES_USER=langgraph_service
   LANGGRAPH_POSTGRES_PASSWORD=langgraph_service_password
   ```

2. **Run the setup script to create the database and user:**
   ```bash
   cd FANalyze_v2.0
   python langgraph/scripts/create_langgraph_service_user.py
   ```

3. **Restart Streamlit** - it should now connect!

### Option 2: Use Separate langgraph-postgres-1 Container
If you want a separate PostgreSQL instance:

1. **Start the container:**
   ```bash
   docker start langgraph-postgres-1
   ```

2. **Add to your `.env` file:**
   ```bash
   LANGGRAPH_POSTGRES_HOST=localhost
   LANGGRAPH_POSTGRES_PORT=5433
   LANGGRAPH_POSTGRES_DB=langgraph_memory
   LANGGRAPH_POSTGRES_USER=langgraph_service
   LANGGRAPH_POSTGRES_PASSWORD=langgraph_service_password
   ```

3. **Run the setup script:**
   ```bash
   python langgraph/scripts/create_langgraph_service_user.py
   ```

4. **Restart Streamlit**

## Verify Connection

Test the connection manually:
```python
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    f"postgresql://{os.getenv('LANGGRAPH_POSTGRES_USER')}:{os.getenv('LANGGRAPH_POSTGRES_PASSWORD')}@{os.getenv('LANGGRAPH_POSTGRES_HOST')}:{os.getenv('LANGGRAPH_POSTGRES_PORT')}/{os.getenv('LANGGRAPH_POSTGRES_DB')}"
)
print("✅ Connected!")
conn.close()
```

## Common Issues

1. **"Missing required environment variables"**
   - Check your `.env` file has all `LANGGRAPH_POSTGRES_*` variables
   - Make sure `.env` is in `FANalyze_v2.0/` directory

2. **"Connection refused"**
   - Make sure PostgreSQL container is running
   - Check the port matches (5432 for kafka-postgres-1, 5433 for langgraph-postgres-1)
   - If using Docker, use `localhost` for host

3. **"Database does not exist"**
   - Run the setup script: `python langgraph/scripts/create_langgraph_service_user.py`

4. **"Authentication failed"**
   - The setup script creates the user - make sure you ran it
   - Check password matches: `langgraph_service_password`



