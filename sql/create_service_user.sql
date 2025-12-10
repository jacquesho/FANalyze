-- Create service user for Airflow and other service connections
-- Username: service
-- Password: airflow

-- Ensure staging schema exists first
CREATE SCHEMA IF NOT EXISTS staging;

-- Create the service user
DO $$
BEGIN
    -- Create the service user if it doesn't exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service') THEN
        CREATE USER service WITH PASSWORD 'airflow' LOGIN;
        RAISE NOTICE 'User "service" created successfully';
    ELSE
        -- If user exists, update password and ensure login privileges
        ALTER USER service WITH PASSWORD 'airflow' LOGIN;
        RAISE NOTICE 'User "service" already exists - password updated';
    END IF;
END
$$;

-- Grant privileges on staging schema
GRANT ALL PRIVILEGES ON SCHEMA staging TO service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO service;

-- Grant privileges on future tables in staging schema
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO service;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON SEQUENCES TO service;

-- Display success message
SELECT 'Service user "service" created/updated successfully with password "airflow"' AS status;

