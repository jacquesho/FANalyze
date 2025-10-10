-- Create staging schema
CREATE SCHEMA IF NOT EXISTS staging;

-- Create user_fanalyze_ingest
CREATE USER user_fanalyze_ingest WITH PASSWORD 'Data4me!';

-- Grant privileges to user_fanalyze_ingest
GRANT ALL PRIVILEGES ON SCHEMA staging TO user_fanalyze_ingest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO user_fanalyze_ingest;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO user_fanalyze_ingest;

-- Create staging_db (if needed as a separate database)
-- Note: This will create the database, but the user will connect to the main postgres database
-- If you need a separate staging_db, uncomment the line below:
-- CREATE DATABASE staging_db OWNER user_fanalyze_ingest;

-- Create a sample table for testing
CREATE TABLE IF NOT EXISTS staging.raw_data (
    id SERIAL PRIMARY KEY,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant privileges on the table
GRANT ALL PRIVILEGES ON TABLE staging.raw_data TO user_fanalyze_ingest;
GRANT USAGE, SELECT ON SEQUENCE staging.raw_data_id_seq TO user_fanalyze_ingest;
