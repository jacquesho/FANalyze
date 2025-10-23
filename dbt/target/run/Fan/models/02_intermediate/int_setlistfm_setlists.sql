
  create or replace   view DB_T4.FAN_INTERMEDIATE.int_setlistfm_setlists
  
  
  
  
  as (
    

-- This model flattens the sets data to get one row per song/setlist item
-- Uses lateral flatten to extract individual songs from the sets structure
--
-- Next steps:
-- 1. Run 'dbt run --select mart_shows mart_setlists' for business logic

with source_data as (
  select
    artist_id,
    artist_name,
    show_id,
    show_date,
    source,
    set_index,
    set_name,
    is_encore,
    song_index,
    song_name,
    cover_artist_name,
    cover_artist_mbid,
    song_info,
    with_artist_name,
    with_artist_mbid,
    ingested_at
  from DB_T4.FAN.raw_setlists
)

select
  artist_id,
  artist_name,
  show_id,
  show_date,
  source,
  set_index,
  set_name,
  is_encore,
  song_index,
  song_name,
  cover_artist_name,
  cover_artist_mbid,
  song_info,
  with_artist_name,
  with_artist_mbid,
  ingested_at
from source_data
  );

