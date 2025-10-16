-- Snowflake DDL for testing schema raw ingestion (JSON-only)
-- Creates schema and two raw tables with VARIANT payloads and metadata

CREATE SCHEMA IF NOT EXISTS testing;

CREATE TABLE IF NOT EXISTS testing.raw_shows (
  artist_id STRING,
  artist_name STRING,
  show_id STRING,
  show_date DATE,
  source VARCHAR DEFAULT 'setlistfm',
  payload VARIANT,
  ingested_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS testing.raw_setlists (
  artist_id STRING,
  artist_name STRING,
  setlist_id STRING,
  show_id STRING,
  source VARCHAR DEFAULT 'setlistfm',
  payload VARIANT,
  ingested_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
);

-- Helpful views (optional)
CREATE VIEW IF NOT EXISTS testing.vw_shows_summary AS
SELECT artist_name, COUNT(*) AS num_shows, MIN(show_date) AS first_show, MAX(show_date) AS last_show
FROM testing.raw_shows
GROUP BY artist_name;


