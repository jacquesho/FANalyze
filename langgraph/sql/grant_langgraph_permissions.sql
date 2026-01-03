-- Grant schema-level privileges for LangGraph service user
-- This script must be run while connected to the langgraph_memory database
-- Usage: psql -U postgres -d langgraph_memory -f grant_langgraph_permissions.sql

-- Grant all privileges on public schema (where LangGraph creates its tables)
GRANT ALL PRIVILEGES ON SCHEMA public TO langgraph_service;

-- Grant privileges on all existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO langgraph_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO langgraph_service;

-- Grant privileges on future tables/sequences (created by PostgresSaver.setup())
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO langgraph_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO langgraph_service;

-- Display success message
SELECT 'LangGraph service user permissions granted successfully on langgraph_memory database' AS status;

