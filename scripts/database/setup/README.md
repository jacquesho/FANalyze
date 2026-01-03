# Database Setup Scripts

This directory contains scripts for initial database setup and configuration.

## Scripts

- **`create_postgres_service_user.py`** - Creates the `service` user with password `airflow` for Airflow and other service connections. Grants privileges on the `staging` schema.

- **`setup_postgres.py`** - Quick setup script for Postgres database. Creates the database and user for the ticket sales demo.

## Usage

### Create Service User

```bash
cd FANalyze_v2.0
python scripts/database/setup/create_postgres_service_user.py
```

### Setup Demo Database

```bash
cd FANalyze_v2.0
python scripts/database/setup/setup_postgres.py
```

## Related SQL Scripts

See `sql/` directory for SQL equivalents:
- `sql/create_service_user.sql`
- `sql/grant_service_permissions.sql`















