

-- This model flattens the raw JSON data to get one row per show
-- Uses lateral flatten to extract individual shows from the JSON structure
--
-- Next steps:
-- 1. Run 'dbt run --select int_setlistfm_setlists' to flatten setlists
-- 2. Run 'dbt run --select mart_shows mart_setlists' for business logic

with source_data as (
  select
    artist_id,
    artist_name,
    artist_mbid,
    show_id,
    show_date,
    source,
    artist_name as artist_name_api,
    artist_mbid as artist_mbid_api,
    venue_name,
    venue_id,
    city_name,
    state_code,
    country_name,
    event_date_str,
    last_updated,
    ingested_at
  from DB_T4.FAN.raw_shows
)

select
  artist_id,
  artist_name,
  artist_mbid,
  show_id,
  show_date,
  source,
  artist_name_api,
  artist_mbid_api,
  venue_name,
  venue_id,
  city_name,
  state_code,
  country_name,
  event_date_str,
  last_updated,
  ingested_at
from source_data