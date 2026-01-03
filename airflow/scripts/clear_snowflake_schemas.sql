-- Script to clear all schemas/tables created by the batch pipeline
-- Run this before testing the batch pipeline to ensure a clean state
-- 
-- Usage: Run via Python script wrapper: python -m scripts.clear_snowflake_schemas

-- Clear FAN_RAW schema tables (raw CSV data)
TRUNCATE TABLE IF EXISTS FAN_RAW.SHOWS_HIS;
TRUNCATE TABLE IF EXISTS FAN_RAW.SHOWS_FUTURE;
TRUNCATE TABLE IF EXISTS FAN_RAW.raw_tickets;

-- Drop staging schema (views) - will be recreated by dbt
DROP SCHEMA IF EXISTS FAN_STAGING CASCADE;

-- Drop intermediate schema (tables) - will be recreated by dbt
DROP SCHEMA IF EXISTS FAN_INTERMEDIATE CASCADE;

-- Drop marts schema (tables) - will be recreated by dbt
DROP SCHEMA IF EXISTS FAN_MARTS CASCADE;

-- Note: FAN_RAW schema and tables will be recreated by the ingestion script
-- The dbt schemas will be recreated by dbt run















