#!/bin/bash

# Create an Airflow user inside the webserver container

CONTAINER_NAME="airflow-webserver"

echo "Creating admin user in $CONTAINER_NAME..."

docker-compose exec "$CONTAINER_NAME" airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password pass

echo "✅ Admin user created: username=admin, password=pass"
