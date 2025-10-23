

-- This model extracts setlist-level data from the JSONL stage
-- One row per song with setlist information

with jsonl_records as (
  select 
    $1 as raw_json,
    metadata$filename as file_name,
    metadata$file_row_number as file_row_number
  from @FAN_RAW.STAGE_RAW_JSON
),

flattened_sets as (
  select
    file_name,
    raw_json:artist_id::string as artist_id,
    raw_json:artist:name::string as artist_name,
    raw_json:show:id::string as show_id,
    to_date(raw_json:show:eventDate::string, 'DD-MM-YYYY') as show_date,
    set_item.value as set_data,
    set_item.index as set_index
  from jsonl_records,
  lateral flatten(input => raw_json:show:sets:set) as set_item
),

flattened_songs as (
  select
    file_name,
    artist_id,
    artist_name,
    show_id,
    show_date,
    set_index,
    set_data:name::string as set_name,
    set_data:encore::boolean as is_encore,
    song.value as song_data,
    song.index as song_index
  from flattened_sets,
  lateral flatten(input => set_data:song) as song
)

select
  artist_id,
  artist_name,
  show_id,
  show_date,
  'setlistfm' as source,
  set_index,
  set_name,
  is_encore,
  song_index,
  song_data:name::string as song_name,
  song_data:cover:name::string as cover_artist_name,
  song_data:cover:mbid::string as cover_artist_mbid,
  song_data:info::string as song_info,
  song_data:with:name::string as with_artist_name,
  song_data:with:mbid::string as with_artist_mbid,
  current_timestamp() as ingested_at
from flattened_songs