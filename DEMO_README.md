# 🎫 Ticket Sales Demo Pipeline

## Overview
This demo shows a complete real-time data pipeline: **Streaming → Postgres → Snowflake**

Perfect for demonstrating real-time data processing for your test next week!

## 🚀 Quick Start

### 1. Setup Postgres Database
```bash
# Install psycopg2 if needed
pip install psycopg2-binary

# Set up the database
python scripts/setup_postgres.py
```

### 2. Run the Demo
```bash
# Interactive demo menu
python scripts/demo_pipeline.py

# Or run individual components:
python scripts/stream_tickets.py --speed 10 --duration 2 --format console
python scripts/stream_to_postgres.py --duration 3 --speed 15
python scripts/postgres_to_snowflake.py
```

## 📋 Demo Components

### 1. **Real-Time Streaming** (`stream_tickets.py`)
- Generates live ticket sales events
- Configurable speed (1x = real-time, 10x = 10x faster)
- Multiple output formats (console, JSON, Kafka)
- Realistic sales patterns based on show characteristics

### 2. **Postgres Integration** (`stream_to_postgres.py`)
- Streams ticket sales directly to Postgres database
- Real-time database writes
- Perfect for live dashboards and analytics

### 3. **Snowflake Transfer** (`postgres_to_snowflake.py`)
- Transfers data from Postgres to Snowflake
- Batch processing for data warehousing
- Complete data pipeline demonstration

### 4. **Complete Demo** (`demo_pipeline.py`)
- Interactive menu with all demos
- Step-by-step walkthrough
- Perfect for presentations

## 🎯 Demo Scenarios

### **Scenario 1: Live Streaming Demo**
```bash
python scripts/stream_tickets.py --speed 20 --duration 2 --format console
```
- Shows live ticket sales happening
- Watch sales build up in real-time
- Great for showing real-time data processing

### **Scenario 2: Data Pipeline Demo**
```bash
# Step 1: Stream to Postgres
python scripts/stream_to_postgres.py --duration 3 --speed 15

# Step 2: Transfer to Snowflake
python scripts/postgres_to_snowflake.py
```
- Complete end-to-end pipeline
- Shows data flow from streaming to data warehouse
- Perfect for architecture discussions

### **Scenario 3: JSON Output Demo**
```bash
python scripts/stream_tickets.py --speed 10 --format jsonl
```
- Shows structured data output
- Perfect for Kafka or other streaming systems
- Great for data format discussions

## 📊 What You'll See

### **Real-Time Sales Events**
```
🎫 Metallica at Madison Square Garden - 7 tickets sold ($1,400) - Total: 7/20000 (0.03%)
🎫 Taylor Swift at TD Garden - 3 tickets sold ($600) - Total: 3/20000 (0.01%)
🎫 The Weeknd at Crypto.com Arena - 5 tickets sold ($1,000) - Total: 5/20000 (0.03%)
```

### **JSON Data Format**
```json
{
  "timestamp": "2025-10-24T12:29:15.979702",
  "show_id": "real_metallica_20251122",
  "artist_name": "Metallica",
  "venue_name": "TD Garden",
  "tickets_sold": 7,
  "revenue": 1400,
  "cumulative_tickets_sold": 7,
  "sales_rate": 0.03
}
```

### **Database Statistics**
```
📊 Final Statistics:
Total sales events: 1,247
Unique shows: 65
Total tickets sold: 45,892
Total revenue: $9,178,400
```

## 🔧 Configuration

### **Postgres Setup**
- Host: localhost:5432
- Database: fanalyze
- User: postgres
- Password: password (change in scripts)

### **Speed Multipliers**
- `--speed 1`: Real-time (1 second = 1 second)
- `--speed 10`: 10x faster (1 second = 0.1 seconds)
- `--speed 20`: 20x faster (1 second = 0.05 seconds)

### **Duration Options**
- `--duration 5`: Run for 5 minutes
- `--max-events 100`: Generate maximum 100 events
- No duration: Run until stopped (Ctrl+C)

## 🎪 Perfect for Your Test!

### **What This Demonstrates:**
✅ **Real-time data streaming**  
✅ **Database integration**  
✅ **Data warehouse pipelines**  
✅ **End-to-end data flow**  
✅ **Scalable architecture**  
✅ **Real-world data patterns**  

### **Key Talking Points:**
- **Real-time processing**: Shows live data streaming
- **Data quality**: Realistic sales patterns and timing
- **Scalability**: Handles multiple shows simultaneously
- **Integration**: Seamless flow between systems
- **Monitoring**: Built-in statistics and tracking

## 🚨 Troubleshooting

### **Postgres Connection Issues**
```bash
# Check if Postgres is running
pg_ctl status

# Start Postgres service
pg_ctl start

# Check port 5432
netstat -an | grep 5432
```

### **Snowflake Connection Issues**
- Verify your Snowflake credentials in `config/api_config.py`
- Check network connectivity to Snowflake
- Ensure proper permissions for table creation

### **Python Dependencies**
```bash
pip install pandas numpy psycopg2-binary
```

## 🎉 Ready to Demo!

Run `python scripts/demo_pipeline.py` and choose your demo scenario. Perfect for showing real-time data processing capabilities!
