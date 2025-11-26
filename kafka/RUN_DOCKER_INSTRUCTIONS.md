# Running Kafka Producer & Consumer with Docker

This guide shows you how to run the Kafka producer and consumer containers using the Dockerfiles.

## Prerequisites

1. **Docker and Docker Compose** installed
2. **`.env` file** configured with required variables (see below)
3. **Network exists** - The compose files use an external network

## Step-by-Step Instructions

### Step 1: Create the Docker Network (if it doesn't exist)

The compose files use an external network. Create it first:

```bash
cd FANalyze_v2.0
docker network create fa-dae2-capstone_kafka_network
```

If the network already exists, you'll get an error - that's fine, just continue.

### Step 2: Start PostgreSQL (from main docker-compose.yaml)

The consumer needs PostgreSQL to store ticket sales. Start it first:

```bash
cd FANalyze_v2.0
docker-compose up -d kafka-postgres
```

Wait for it to be healthy (check with `docker-compose ps`).

### Step 3: Start Kafka Infrastructure

Start Kafka (and optionally Kafdrop UI):

```bash
# Start Kafka only
docker-compose -f docker-compose-kafka.yml up -d kafka

# OR start Kafka + Kafdrop UI (recommended for monitoring)
docker-compose -f docker-compose-kafka.yml --profile ui up -d
```

**Verify Kafka is running:**
```bash
docker-compose -f docker-compose-kafka.yml ps
```

You should see `kafka` (and optionally `kafdrop`) with status "healthy".

**Access Kafdrop UI (if started):**
- Open browser to http://localhost:9000
- You can view topics, messages, and consumer groups here

### Step 4: Build and Start Producer & Consumer Containers

Now start the producer and consumer using the `app` profile:

```bash
# Build and start both containers
docker-compose -f docker-compose-kafka.yml --profile app up -d --build
```

This will:
- Build `kafka/Dockerfile.producer` → creates `ticket-producer` container
- Build `kafka/Dockerfile.consumer` → creates `postgres-consumer` container
- Start both containers

### Step 5: Monitor the Containers

**View logs for both:**
```bash
docker-compose -f docker-compose-kafka.yml logs -f ticket-producer postgres-consumer
```

**View logs separately:**
```bash
# Producer logs
docker-compose -f docker-compose-kafka.yml logs -f ticket-producer

# Consumer logs
docker-compose -f docker-compose-kafka.yml logs -f postgres-consumer
```

**Check container status:**
```bash
docker-compose -f docker-compose-kafka.yml ps
```

### Step 6: Verify Data Flow

**Check Kafka topic:**
```bash
# List topics
docker exec -it $(docker ps -q -f name=kafka) kafka-topics --list --bootstrap-server kafka:9092

# Describe ticket_sales topic
docker exec -it $(docker ps -q -f name=kafka) kafka-topics --describe --topic ticket_sales --bootstrap-server kafka:9092
```

**Check PostgreSQL data:**
```bash
# Connect to PostgreSQL
docker exec -it $(docker ps -q -f name=kafka-postgres) psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-capstone}

# Then run SQL:
SELECT COUNT(*) FROM staging.ticket_sales;
SELECT * FROM staging.ticket_sales ORDER BY created_at DESC LIMIT 10;
```

**Or use Kafdrop UI:**
- Go to http://localhost:9000
- Click on `ticket_sales` topic
- View messages in real-time
- Check consumer groups

## Quick Reference Commands

### Start Everything
```bash
# 1. PostgreSQL
docker-compose up -d kafka-postgres

# 2. Kafka + UI
docker-compose -f docker-compose-kafka.yml --profile ui up -d

# 3. Producer & Consumer
docker-compose -f docker-compose-kafka.yml --profile app up -d --build
```

### Stop Everything
```bash
# Stop producer/consumer
docker-compose -f docker-compose-kafka.yml --profile app down

# Stop Kafka + UI
docker-compose -f docker-compose-kafka.yml --profile ui down

# Stop PostgreSQL
docker-compose down kafka-postgres
```

### Restart Services
```bash
# Restart producer/consumer
docker-compose -f docker-compose-kafka.yml --profile app restart

# Restart Kafka
docker-compose -f docker-compose-kafka.yml restart kafka
```

## Required Environment Variables

Make sure your `.env` file has these variables:

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=capstone
POSTGRES_PORT=5432

# Kafka (for Docker, these are set automatically in compose)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=ticket_sales

# Snowflake (required for producer)
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your-username
SNOWFLAKE_ROLE=your-role
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=your-schema
SNOWFLAKE_KEYPAIR_PATH=.secrets/rsa_key.p8
```

## Troubleshooting

### Network Issues
If you get network errors:
```bash
# Check if network exists
docker network ls | grep kafka

# Create if missing
docker network create fa-dae2-capstone_kafka_network
```

### Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose-kafka.yml logs ticket-producer
docker-compose -f docker-compose-kafka.yml logs postgres-consumer

# Rebuild containers
docker-compose -f docker-compose-kafka.yml --profile app build --no-cache
docker-compose -f docker-compose-kafka.yml --profile app up -d
```

### PostgreSQL Connection Errors
- Ensure PostgreSQL is running: `docker-compose ps`
- Check PostgreSQL is healthy: `docker-compose ps kafka-postgres`
- Verify environment variables are set correctly

### Kafka Connection Errors
- Ensure Kafka is healthy: `docker-compose -f docker-compose-kafka.yml ps`
- Check Kafka logs: `docker-compose -f docker-compose-kafka.yml logs kafka`
- Wait for Kafka to be fully ready (can take 30-60 seconds)

### No Messages Appearing
- Check producer logs for errors
- Verify Snowflake credentials are correct
- Check if producer found artists/shows in Snowflake
- Verify topic exists: `docker exec -it $(docker ps -q -f name=kafka) kafka-topics --list --bootstrap-server kafka:9092`

## What You Should See

**Producer logs should show:**
```
🎫 Produced message #1: Artist Name at Venue Name - X tickets ($XXX.XX) - Total: XXX/XXXX (XX%)
```

**Consumer logs should show:**
```
✅ Inserted sale for Artist Name - X tickets at Venue Name
Progress: 10 messages processed, 10 rows written
```

**In Kafdrop UI:**
- Topic `ticket_sales` with 3 partitions
- Messages appearing in real-time
- Consumer group `ticket-sales-consumer-group` consuming messages

**In PostgreSQL:**
- Table `staging.ticket_sales` with rows being inserted
- Data includes: artist_name, venue_name, tickets_sold, revenue, etc.

