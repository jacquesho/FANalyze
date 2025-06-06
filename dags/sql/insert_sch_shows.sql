-- ✅ Create or replace stage for shows
CREATE OR REPLACE STAGE DB_FANALYZE.FANALYZE.RAW_SHOWS_STAGE;

{% set csv_paths = ti.xcom_pull(task_ids='list_csv_files', key='return_value') %}
{% if csv_paths %}
  {% for path in csv_paths %}
PUT file://{{ path }} @DB_FANALYZE.FANALYZE.RAW_SHOWS_STAGE AUTO_COMPRESS=FALSE;
  {% endfor %}
{% else %}
  -- No CSV files found by list_csv_files
{% endif %}

-- ✅ Insert using a named file format (must be created beforehand)
-- ❗ Make sure this exists:
-- CREATE OR REPLACE FILE FORMAT DB_FANALYZE.STAGING.SHOWS_CSV_FORMAT
--   TYPE = 'CSV'
--   SKIP_HEADER = 1
--   FIELD_DELIMITER = ','
--   FIELD_OPTIONALLY_ENCLOSED_BY = '"'
--   NULL_IF = ('\\N', 'NULL', '');

-- insert_sch_shows.sql (comes in via CSV file)
INSERT INTO DB_FANALYZE.FANALYZE.STG_SHOWS_SCH (
  SHOW_ID,
  ARTIST_ID,
  ARTIST_NAME,
  EVENT_DATE,
  VENUE,
  CITY,
  COUNTRY,
  TOUR_NAME,
  TICKET_TIER,
  SIMULATED_PRICE_USD,
  LOAD_TYPE
)
WITH raw_csv AS (
  SELECT
    $4  AS show_id,
    $1  AS artist_id,
    $2  AS artist_name,
    TO_DATE($3, 'YYYY-MM-DD') AS event_date,
    $5  AS venue,
    $6  AS city,
    $7  AS country,
    $8  AS tour_name,
    $9  AS ticket_tier,
    TRY_CAST($10 AS FLOAT) AS simulated_price_usd,
    'Scheduled' AS load_type
  FROM @DB_FANALYZE.FANALYZE.RAW_SHOWS_STAGE
  (FILE_FORMAT => DB_FANALYZE.FANALYZE.CSV_FORMAT)
)
SELECT * FROM raw_csv;
