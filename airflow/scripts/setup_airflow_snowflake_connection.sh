#!/bin/bash

# Script to set up Airflow Snowflake connection using .env variables
# Run this script from the FANalyze_v2.0 directory
# Usage: ./airflow/scripts/setup_airflow_snowflake_connection.sh

set -e

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found in current directory"
    echo "Please create a .env file with your Snowflake credentials"
    exit 1
fi

# Source the .env file
source .env

# Check if Airflow is running
if ! docker-compose -f docker-compose-airflow.yml ps | grep -q "airflow-apiserver"; then
    echo "Error: Airflow is not running. Start it first: docker-compose -f docker-compose-airflow.yml up -d"
    exit 1
fi

# Read and encode private key content (base64 encoding for safe transmission)
# Use SNOWFLAKE_PRIVATE_KEY_FILE_PATH from .env, default to .secrets/rsa_key.p8 if not set
SNOWFLAKE_PRIVATE_KEY_FILE_PATH="${SNOWFLAKE_PRIVATE_KEY_FILE_PATH:-.secrets/rsa_key.p8}"

if [ ! -f "$SNOWFLAKE_PRIVATE_KEY_FILE_PATH" ]; then
    echo "Error: Private key file not found at $SNOWFLAKE_PRIVATE_KEY_FILE_PATH"
    echo "Please ensure your Snowflake private key file exists at the specified path"
    exit 1
fi

# Base64 encode the private key (compatible with both macOS and Linux)
PRIVATE_KEY_CONTENT=$(cat "$SNOWFLAKE_PRIVATE_KEY_FILE_PATH" | base64 | tr -d '\n')

echo "Setting up Snowflake connection: snowflake_default"

# Delete existing connection if it exists
docker-compose -f docker-compose-airflow.yml exec -T airflow-apiserver airflow connections delete snowflake_default 2>/dev/null || true

# Add new connection
docker-compose -f docker-compose-airflow.yml exec -T airflow-apiserver airflow connections add 'snowflake_default' \
    --conn-type 'snowflake' \
    --conn-login "$SNOWFLAKE_USER" \
    --conn-password "$SNOWFLAKE_PRIVATE_KEY_FILE_PWD" \
    --conn-schema "$SNOWFLAKE_SCHEMA" \
    --conn-extra "{\"account\": \"$SNOWFLAKE_ACCOUNT\", \"warehouse\": \"$SNOWFLAKE_WAREHOUSE\", \"database\": \"$SNOWFLAKE_DATABASE\", \"role\": \"$SNOWFLAKE_ROLE\", \"private_key_content\": \"$PRIVATE_KEY_CONTENT\"}"

echo "✅ Snowflake connection setup complete"

