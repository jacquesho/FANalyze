#!/bin/bash

# Script to set up Airflow PostgreSQL connection using .env variables
# Run this script from the FANalyze_v2.0 directory
# Usage: ./airflow/scripts/setup_airflow_postgres_connection.sh

set -e

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found in current directory"
    echo "Please create a .env file with your PostgreSQL credentials"
    exit 1
fi

# Source the .env file
source .env

# Check if Airflow is running
if ! docker-compose -f docker-compose-airflow.yml ps | grep -q "airflow-apiserver"; then
    echo "Error: Airflow is not running. Start it first: docker-compose -f docker-compose-airflow.yml up -d"
    exit 1
fi

echo "Setting up PostgreSQL connection: postgres_kafka_default"

# Delete existing connection if it exists
docker-compose -f docker-compose-airflow.yml exec -T airflow-apiserver airflow connections delete postgres_kafka_default 2>/dev/null || true

# Add new connection
docker-compose -f docker-compose-airflow.yml exec -T airflow-apiserver airflow connections add 'postgres_kafka_default' \
    --conn-type 'postgres' \
    --conn-login "$POSTGRES_USER" \
    --conn-password "$POSTGRES_PASSWORD" \
    --conn-host "kafka-postgres" \
    --conn-port "${POSTGRES_PORT:-5432}" \
    --conn-schema "$POSTGRES_DB"

echo "✅ PostgreSQL connection setup complete"

