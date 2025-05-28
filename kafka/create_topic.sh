#!/usr/bin/env bash
set -e

# Load environment variables from .env-kafka
export $(grep -v '^#' .env-kafka | xargs)

# Get the Kafka container ID
KAFKA_CONTAINER=$(docker-compose ps -q kafka)

# Create the topic
docker exec -i "$KAFKA_CONTAINER" \
  kafka-topics --create \
    --topic concert_events \
    --bootstrap-server "$KAFKA_BOOTSTRAP" \
    --partitions 1 \
    --replication-factor 1

echo "✅ Topic 'concert_events' created"
