# Kafka Infrastructure for FANalyze v2.0

This directory contains the Kafka producer and consumer infrastructure for streaming ticket sales events.

## Directory Structure

```
kafka/
├── base_producer.py           # Infrastructure: client, send, retry, logging
├── base_consumer.py           # Infrastructure: client, poll, retry, logging
├── producers/
│   └── ticket_producer.py     # Business logic: generate ticket sales, publish to Kafka
├── consumers/
│   └── postgres_consumer.py   # Business logic: consume messages, insert to PostgreSQL
└── utils/
    └── serializers.py         # JSON serialization utilities
```

## Architecture

### Base Classes (Infrastructure Layer)

**BaseProducer** handles:
- Kafka client configuration
- Message sending with automatic retry
- Topic creation/validation
- Error handling and logging
- Clean shutdown

**BaseConsumer** handles:
- Kafka client configuration
- Message polling with error handling
- Offset management (manual commit)
- Error handling and logging
- Clean shutdown

### Business Logic Classes

**TicketProducer** extends BaseProducer:
- Queries Snowflake for active artists and shows
- Generates realistic ticket sales events
- Uses `artist_name` as message key (for partitioning)
- Publishes to `ticket_sales` topic

**PostgresConsumer** extends BaseConsumer:
- Consumes from `ticket_sales` topic
- Deserializes JSON messages
- Inserts into `staging.ticket_sales` table
- Creates table/indexes if needed

## Partitioning Strategy

- **Topic**: `ticket_sales` (3 partitions)
- **Key**: `artist_name` (determines partition via hash)
- **Distribution**: Kafka automatically distributes artists across 3 partitions
- **Benefits**: Natural load balancing, enables per-artist processing if needed

## Environment Variables

Required in `.env` file:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:29092  # For UV run
# KAFKA_BOOTSTRAP_SERVERS=kafka:9092      # For Docker Compose
KAFKA_TOPIC=ticket_sales
KAFKA_GROUP_ID=ticket-sales-consumer-group

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

# Snowflake Configuration (for producer)
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your-username
SNOWFLAKE_ROLE=your-role
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=your-schema
SNOWFLAKE_KEYPAIR_PATH=.secrets/rsa_key.p8
```

## Usage

### Start the Consumer

```bash
cd FANalyze_v2.0
uv run python kafka/consumers/postgres_consumer.py
```

The consumer will:
- Connect to Kafka and PostgreSQL
- Create `staging.ticket_sales` table if needed
- Start consuming messages
- Insert events into PostgreSQL

### Start the Producer

```bash
cd FANalyze_v2.0
uv run python kafka/producers/ticket_producer.py
```

The producer will:
- Query Snowflake for active artists
- Create `ticket_sales` topic (3 partitions) if needed
- Generate ticket sales events
- Publish to Kafka with `artist_name` as key
- Send messages every 10 seconds

## Data Flow

```
Snowflake (artists & shows)
    ↓
TicketProducer
    ↓
Kafka Topic: ticket_sales (3 partitions, keyed by artist_name)
    ↓
PostgresConsumer
    ↓
PostgreSQL: staging.ticket_sales
    ↓
Snowflake (via sync script)
    ↓
Dashboard (queries by artist_name)
```

## Extending the System

### Adding a New Producer

1. Create new file in `kafka/producers/`
2. Extend `BaseProducer`
3. Implement business logic:
   - Data fetching
   - Event generation
   - Message key selection

Example:
```python
from kafka.base_producer import BaseProducer
from kafka.utils.serializers import serialize_json

class WeatherProducer(BaseProducer):
    def __init__(self):
        super().__init__(client_id="weather-producer")
        self.topic = "weather_data"
    
    def run(self):
        # Your business logic here
        data = self.fetch_weather_data()
        value = serialize_json(data)
        self.send(self.topic, key="weather", value=value)
```

### Adding a New Consumer

1. Create new file in `kafka/consumers/`
2. Extend `BaseConsumer`
3. Implement business logic:
   - Message processing
   - Data transformation
   - Storage/action

Example:
```python
from kafka.base_consumer import BaseConsumer
from kafka.utils.serializers import deserialize_json

class AnalyticsConsumer(BaseConsumer):
    def __init__(self):
        super().__init__(group_id="analytics-consumer")
        self.subscribe(["ticket_sales"])
    
    def process_message(self, msg):
        data = deserialize_json(msg.value())
        # Your processing logic here
        return True
```

## Testing

### Verify Kafka Connection

```bash
# Check if Kafka is running
docker-compose -f docker-compose-kafka.yml ps

# List topics
docker exec -it $(docker ps -q -f name=kafka) kafka-topics --list --bootstrap-server kafka:9092
```

### Verify PostgreSQL Data

```sql
-- Check table exists
SELECT COUNT(*) FROM staging.ticket_sales;

-- View recent sales
SELECT artist_name, SUM(tickets_sold) as total_tickets, SUM(revenue) as total_revenue
FROM staging.ticket_sales
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY artist_name
ORDER BY total_revenue DESC;
```

## Troubleshooting

### Common Issues

1. **Kafka connection refused**
   - Check `KAFKA_BOOTSTRAP_SERVERS` in `.env`
   - Verify Kafka is running: `docker-compose ps`

2. **PostgreSQL connection errors**
   - Check PostgreSQL credentials in `.env`
   - Ensure `staging` schema exists

3. **No artists found**
   - Producer falls back to sample data if Snowflake fails
   - Check Snowflake credentials and connection

4. **Import errors**
   - Run `uv sync` to install dependencies
   - Ensure `confluent-kafka` is installed

## Next Steps

- Add monitoring/metrics collection
- Implement dead letter queue for failed messages
- Add batch processing for better performance
- Create dashboard for real-time visualization
- Add schema validation (Avro/Protobuf)



