# Kafka Docker Setup for FANalyze v2.0

This document explains how to use the separate `docker-compose-kafka.yml` file for Kafka infrastructure.

## Quick Start

### Start Kafka

```bash
# Start Kafka service
docker-compose -f docker-compose-kafka.yml up -d kafka

# Verify it's running
docker-compose -f docker-compose-kafka.yml ps
```

### Start Kafka + UI (Kafdrop)

```bash
# Start Kafka and Kafdrop UI
docker-compose -f docker-compose-kafka.yml --profile ui up -d

# Access Kafdrop at http://localhost:9000
```

### Stop Kafka

```bash
# Stop Kafka (keeps data)
docker-compose -f docker-compose-kafka.yml stop

# Stop and remove containers (keeps data)
docker-compose -f docker-compose-kafka.yml down

# Stop and remove everything including data
docker-compose -f docker-compose-kafka.yml down -v
```

## Network Configuration

The Kafka compose file uses the same external network as your main `docker-compose.yaml`:
- **Network**: `fa-dae2-capstone_kafka_network`
- This allows Kafka to communicate with PostgreSQL in your main compose

## Services

### Kafka
- **Ports**: 
  - `9092` - Docker network access
  - `29092` - Host access (for UV run)
- **Mode**: KRaft (no ZooKeeper needed)
- **Health Check**: Automatically verifies Kafka is ready

### Kafdrop (Optional UI)
- **Port**: `9000`
- **Access**: http://localhost:9000
- **Profile**: Only starts with `--profile ui` flag
- **Features**: 
  - View topics and messages
  - Monitor consumer groups
  - Browse partitions
  - Publish test messages

## Common Commands

### Check Status
```bash
docker-compose -f docker-compose-kafka.yml ps
```

### View Logs
```bash
# Kafka logs
docker-compose -f docker-compose-kafka.yml logs kafka

# Follow logs
docker-compose -f docker-compose-kafka.yml logs -f kafka
```

### Restart Services
```bash
docker-compose -f docker-compose-kafka.yml restart kafka
```

### List Topics
```bash
docker exec -it $(docker ps -q -f name=kafka) kafka-topics --list --bootstrap-server kafka:9092
```

### Describe Topic
```bash
docker exec -it $(docker ps -q -f name=kafka) kafka-topics --describe --topic ticket_sales --bootstrap-server kafka:9092
```

## Working with Main Compose

Since Kafka is in a separate file, you can:

1. **Start PostgreSQL only**:
   ```bash
   docker-compose up -d kafka-postgres
   ```

2. **Start Kafka only**:
   ```bash
   docker-compose -f docker-compose-kafka.yml up -d kafka
   ```

3. **Start both**:
   ```bash
   docker-compose up -d kafka-postgres
   docker-compose -f docker-compose-kafka.yml up -d kafka
   ```

## Troubleshooting

### Kafka won't start
- Check if port 29092 or 9092 is already in use
- Verify Docker has enough resources (≥4GB RAM)
- Check logs: `docker-compose -f docker-compose-kafka.yml logs kafka`

### Can't connect from host
- Ensure you're using `localhost:29092` in your `.env`
- Verify Kafka is healthy: `docker-compose -f docker-compose-kafka.yml ps`

### Network issues
- Verify network exists: `docker network ls | grep kafka`
- If missing, create it: `docker network create fa-dae2-capstone_kafka_network`

## Running Producer/Consumer

You have two options:

### Option 1: UV Run (Development - Recommended)

```bash
# Terminal 1: Consumer
uv run python kafka/consumers/postgres_consumer.py

# Terminal 2: Producer
uv run python kafka/producers/ticket_producer.py
```

**Pros**: Easy debugging, fast iteration, direct log access

### Option 2: Docker (Production-like/Demos)

```bash
# IMPORTANT: Start PostgreSQL first (from main compose)
docker-compose up -d kafka-postgres

# Start Kafka infrastructure
docker-compose -f docker-compose-kafka.yml up -d kafka

# Then start producer and consumer as containers
docker-compose -f docker-compose-kafka.yml --profile app up -d --build

# View logs
docker-compose -f docker-compose-kafka.yml logs -f ticket-producer postgres-consumer

# Stop containers
docker-compose -f docker-compose-kafka.yml --profile app down
```

**Pros**: Production-like, orchestrated, container logs

**Note**: PostgreSQL must be started from the main `docker-compose.yaml` first, since it's not in the Kafka compose file.

## Environment Variables

Make sure your `.env` file has:
```bash
# For UV run (recommended for development)
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
POSTGRES_HOST=localhost

# For Docker containers (automatically set in compose)
# KAFKA_BOOTSTRAP_SERVERS=kafka:9092
# POSTGRES_HOST=kafka-postgres
```

The Docker services automatically use the correct internal network addresses.

