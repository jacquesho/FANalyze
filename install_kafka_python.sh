#!/bin/bash

# List of target containers
containers=$(docker ps --format '{{.Names}}' | grep 'fanalyze-airflow')

# Package to install
PACKAGE="kafka-python"

for container in $containers; do
  echo "🔍 Checking $container"

  # Try install
  docker exec -it "$container" bash -c "python -m pip install $PACKAGE"

  # Verify installation
  docker exec -it "$container" python -c "from kafka import KafkaProducer; print('✅ $container: KafkaProducer is available')" \
    || echo "❌ $container: KafkaProducer NOT available"
done
