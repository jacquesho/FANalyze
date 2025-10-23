

-- This model reads from the raw tables and provides a unified view of the data
-- One row per JSON file with metadata and summary information
--
-- Next steps:
-- 1. Run 'dbt run --select int_setlistfm_shows' to flatten shows
-- 2. Run 'dbt run --select int_setlistfm_setlists' to flatten setlists

with raw_shows_summary as (
  select
    source,
    count(distinct show_id) as total_shows,
    count(distinct artist_id) as total_artists,
    min(ingested_at) as first_ingested_at,
    max(ingested_at) as last_ingested_at
  from DB_T4.FAN_RAW.raw_shows
  group by source
),

raw_setlists_summary as (
  select
    source,
    count(*) as total_songs,
    count(distinct show_id) as shows_with_setlists
  from DB_T4.FAN_RAW.raw_setlists
  group by source
)

select
  'setlistfm' as source,
  total_artists,
  total_shows,
  total_songs,
  shows_with_setlists,
  first_ingested_at as fetched_at,
  last_ingested_at as last_updated,
  current_timestamp() as ingested_at
from raw_shows_summary
left join raw_setlists_summary using (source)