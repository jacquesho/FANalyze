-- Create staging schema
CREATE SCHEMA IF NOT EXISTS staging;

-- Create staging_user
CREATE USER staging_user WITH PASSWORD 'staging_password';

-- Grant privileges to staging_user
GRANT ALL PRIVILEGES ON SCHEMA staging TO staging_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO staging_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO staging_user;

-- Create staging_db (if needed as a separate database)
-- Note: This will create the database, but the user will connect to the main postgres database
-- If you need a separate staging_db, uncomment the line below:
-- CREATE DATABASE staging_db OWNER staging_user;

-- Create a sample table for testing
CREATE TABLE IF NOT EXISTS staging.raw_data (
    id SERIAL PRIMARY KEY,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant privileges on the table
GRANT ALL PRIVILEGES ON TABLE staging.raw_data TO staging_user;
GRANT USAGE, SELECT ON SEQUENCE staging.raw_data_id_seq TO staging_user;
