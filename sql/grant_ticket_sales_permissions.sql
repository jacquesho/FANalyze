-- Grant permissions on ticket_sales table to service user
-- Run this after the ticket_sales table is created by the Kafka consumer

-- Grant all privileges on the ticket_sales table
GRANT ALL PRIVILEGES ON TABLE staging.ticket_sales TO service;

-- Grant privileges on sequences (if any)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO service;

-- Display success
SELECT 'Permissions granted on ticket_sales table to service user' AS status;















