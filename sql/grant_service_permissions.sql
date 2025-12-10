-- Grant owner-like permissions to service user on staging schema
-- This allows the service user to read, write, and modify tables created by other users

-- Grant schema usage
GRANT USAGE ON SCHEMA staging TO service;

-- Grant all privileges on all existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO service;

-- Grant all privileges on all existing sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO service;

-- Set default privileges for future tables created by any user
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO service;

-- Set default privileges for future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON SEQUENCES TO service;

-- Specifically grant permissions on ticket_sales table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables 
               WHERE table_schema = 'staging' AND table_name = 'ticket_sales') THEN
        -- Grant all privileges including ALTER (to add/modify columns)
        EXECUTE 'GRANT ALL PRIVILEGES ON TABLE staging.ticket_sales TO service';
        -- Change ownership to service user (required for ALTER TABLE operations)
        EXECUTE 'ALTER TABLE staging.ticket_sales OWNER TO service';
        RAISE NOTICE 'Granted permissions and ownership on existing ticket_sales table';
    ELSE
        RAISE NOTICE 'ticket_sales table does not exist yet - permissions will be granted when created';
    END IF;
END
$$;

-- Display success
SELECT 'Service user permissions configured successfully' AS status;

