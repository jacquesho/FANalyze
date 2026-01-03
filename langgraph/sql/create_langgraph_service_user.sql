-- Create LangGraph service user and database
-- Username: langgraph_service
-- Password: langgraph_service_password
-- Database: langgraph_memory

-- Create the langgraph_memory database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langgraph_memory') THEN
        CREATE DATABASE langgraph_memory;
        RAISE NOTICE 'Database "langgraph_memory" created successfully';
    ELSE
        RAISE NOTICE 'Database "langgraph_memory" already exists';
    END IF;
END
$$;

-- Create the langgraph_service user
DO $$
BEGIN
    -- Create the langgraph_service user if it doesn't exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'langgraph_service') THEN
        CREATE USER langgraph_service WITH PASSWORD 'langgraph_service_password' LOGIN;
        RAISE NOTICE 'User "langgraph_service" created successfully';
    ELSE
        -- If user exists, update password and ensure login privileges
        ALTER USER langgraph_service WITH PASSWORD 'langgraph_service_password' LOGIN;
        RAISE NOTICE 'User "langgraph_service" already exists - password updated';
    END IF;
END
$$;

-- Grant connection and creation privileges on langgraph_memory database
GRANT CONNECT ON DATABASE langgraph_memory TO langgraph_service;
GRANT CREATE ON DATABASE langgraph_memory TO langgraph_service;

-- Note: Schema-level privileges must be granted while connected to langgraph_memory database
-- Run the following commands after connecting to langgraph_memory:
-- 
-- GRANT ALL PRIVILEGES ON SCHEMA public TO langgraph_service;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO langgraph_service;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO langgraph_service;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO langgraph_service;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO langgraph_service;

-- Display success message
SELECT 'LangGraph service user "langgraph_service" and database "langgraph_memory" created successfully' AS status;

