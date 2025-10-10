-- Create staging schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS staging;

-- Create test_ingest table for CSV data ingestion
CREATE TABLE IF NOT EXISTS staging.test_ingest (
    id INTEGER PRIMARY KEY,
    data_content TEXT,
    file_name VARCHAR(255),
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_fanalyze_ingest user for data ingestion
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user_fanalyze_ingest') THEN
        CREATE USER user_fanalyze_ingest WITH PASSWORD 'fanalyze_ingest_password';
    END IF;
END
$$;

-- Grant permissions to user_fanalyze_ingest
GRANT ALL PRIVILEGES ON SCHEMA staging TO user_fanalyze_ingest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO user_fanalyze_ingest;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO user_fanalyze_ingest;

-- Grant permissions to staging_user (for backward compatibility)
GRANT ALL PRIVILEGES ON SCHEMA staging TO staging_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO staging_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO staging_user;

-- Create index on loaded_at for performance
CREATE INDEX IF NOT EXISTS idx_test_ingest_loaded_at ON staging.test_ingest(loaded_at);

-- Insert sample data for testing (optional)
-- INSERT INTO staging.test_ingest (id, data_content, file_name) VALUES 
-- (1, 'Sample CSV data 1', 'test1.csv'),
-- (2, 'Sample CSV data 2', 'test2.csv'),
-- (3, 'Sample CSV data 3', 'test3.csv');
