
  
    

create or replace table DB_T4.FAN.raw_setlists
    
    
    
    as (

-- This model extracts setlist-level data from the JSON stage and loads it into the raw setlists table
-- One row per song with setlist information

with json_files as (
  select 
    $1 as raw_json,
    metadata$filename as file_name,
    metadata$file_row_number as file_row_number
  from @DB_T4.FAN_RAW.STAGE_RAW_JSON
),

flattened_artists as (
  select
    file_name,
    artist.key as artist_id,
    artist.value:artist as artist_info,
    artist.value:shows as shows_array
  from json_files,
  lateral flatten(input => raw_json:data) as artist
),

flattened_shows as (
  select
    file_name,
    artist_id,
    artist_info:name::string as artist_name,
    artist_info:mbid::string as artist_mbid,
    show.value as show_data,
    show.index as show_index
  from flattened_artists,
  lateral flatten(input => shows_array) as show
),

flattened_sets as (
  select
    file_name,
    artist_id,
    artist_name,
    artist_mbid,
    show_data:id::string as show_id,
    to_date(show_data:eventDate::string, 'DD-MM-YYYY') as show_date,
    set_item.value as set_data,
    set_item.index as set_index
  from flattened_shows,
  lateral flatten(input => show_data:sets:set) as set_item
),

flattened_songs as (
  select
    file_name,
    artist_id,
    artist_name,
    artist_mbid,
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
    )
;


  