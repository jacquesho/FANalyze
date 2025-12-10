# Docker Compose Commands for Airflow

## Quick Reference

### Start Airflow
```bash
cd FANalyze_v2.0
docker-compose -f docker-compose-airflow.yml up -d
```

### Stop Airflow
```bash
docker-compose -f docker-compose-airflow.yml stop
```

### Stop and Remove Containers (keeps data)
```bash
docker-compose -f docker-compose-airflow.yml down
```

### Stop and Remove Everything (including volumes - deletes data!)
```bash
docker-compose -f docker-compose-airflow.yml down -v
```

## Detailed Commands

### Starting Airflow

**Start in detached mode (background):**
```bash
docker-compose -f docker-compose-airflow.yml up -d
```

**Start and view logs:**
```bash
docker-compose -f docker-compose-airflow.yml up
```

**Start and rebuild images:**
```bash
docker-compose -f docker-compose-airflow.yml up -d --build
```

**Start specific services only:**
```bash
# Start just webserver and scheduler
docker-compose -f docker-compose-airflow.yml up -d airflow-webserver airflow-scheduler
```

### Stopping Airflow

**Stop containers (keeps them for restart):**
```bash
docker-compose -f docker-compose-airflow.yml stop
```

**Stop and remove containers (keeps volumes/data):**
```bash
docker-compose -f docker-compose-airflow.yml down
```

**Stop and remove everything including volumes (⚠️ deletes Airflow database!):**
```bash
docker-compose -f docker-compose-airflow.yml down -v
```

### Restarting Services

**Restart all services:**
```bash
docker-compose -f docker-compose-airflow.yml restart
```

**Restart specific service:**
```bash
docker-compose -f docker-compose-airflow.yml restart airflow-webserver
docker-compose -f docker-compose-airflow.yml restart airflow-scheduler
```

### Viewing Logs

**View all logs:**
```bash
docker-compose -f docker-compose-airflow.yml logs
```

**Follow logs (like tail -f):**
```bash
docker-compose -f docker-compose-airflow.yml logs -f
```

**View specific service logs:**
```bash
docker-compose -f docker-compose-airflow.yml logs -f airflow-webserver
docker-compose -f docker-compose-airflow.yml logs -f airflow-scheduler
docker-compose -f docker-compose-airflow.yml logs -f airflow-init
```

**View last 100 lines:**
```bash
docker-compose -f docker-compose-airflow.yml logs --tail=100
```

### Checking Status

**Check container status:**
```bash
docker-compose -f docker-compose-airflow.yml ps
```

**Check if services are healthy:**
```bash
docker-compose -f docker-compose-airflow.yml ps
# Look for "healthy" status
```

### Rebuilding

**Rebuild images:**
```bash
docker-compose -f docker-compose-airflow.yml build
```

**Rebuild without cache:**
```bash
docker-compose -f docker-compose-airflow.yml build --no-cache
```

**Rebuild and restart:**
```bash
docker-compose -f docker-compose-airflow.yml up -d --build
```

## Common Workflows

### First Time Setup
```bash
# 1. Set Airflow UID (Linux/Mac)
export AIRFLOW_UID=$(id -u)

# 2. Build and start
docker-compose -f docker-compose-airflow.yml up -d --build

# 3. Check logs
docker-compose -f docker-compose-airflow.yml logs -f

# 4. Access UI at http://localhost:8080
```

### Daily Development
```bash
# Start
docker-compose -f docker-compose-airflow.yml up -d

# Stop
docker-compose -f docker-compose-airflow.yml stop

# Or down (removes containers but keeps data)
docker-compose -f docker-compose-airflow.yml down
```

### After Code Changes
```bash
# Rebuild and restart
docker-compose -f docker-compose-airflow.yml up -d --build

# Or just restart (if no Dockerfile changes)
docker-compose -f docker-compose-airflow.yml restart
```

### Clean Slate (⚠️ Deletes all data!)
```bash
# Stop and remove everything
docker-compose -f docker-compose-airflow.yml down -v

# Rebuild from scratch
docker-compose -f docker-compose-airflow.yml up -d --build
```

## Prerequisites

Before starting Airflow, ensure:

1. **Network exists:**
   ```bash
   docker network create fa-dae2-capstone_kafka_network
   ```

2. **PostgreSQL is running** (if your DAGs need it):
   ```bash
   docker-compose up -d kafka-postgres
   ```

3. **Kafka is running** (if your DAGs use Kafka):
   ```bash
   docker-compose -f docker-compose-kafka.yml up -d kafka
   ```

## Access Points

- **Airflow UI**: http://localhost:8080
  - Username: `airflow`
  - Password: `airflow` (default)

## Troubleshooting

### Port 8080 already in use
```bash
# Change port in docker-compose-airflow.yml:
ports:
  - "8081:8080"  # Use 8081 instead
```

### Containers won't start
```bash
# Check logs
docker-compose -f docker-compose-airflow.yml logs

# Check status
docker-compose -f docker-compose-airflow.yml ps
```

### DAGs not appearing
```bash
# Check scheduler logs
docker-compose -f docker-compose-airflow.yml logs airflow-scheduler

# Restart scheduler
docker-compose -f docker-compose-airflow.yml restart airflow-scheduler
```

