
  
    

create or replace table DB_T4.FAN.raw_shows
    
    
    
    as (

-- This model extracts show-level data from the JSON stage and loads it into the raw shows table
-- One row per show with basic show information

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
)

select
  artist_id,
  artist_name,
  show_data:id::string as show_id,
  to_date(show_data:eventDate::string, 'DD-MM-YYYY') as show_date,
  'setlistfm' as source,
  artist_name as artist_name_api,
  artist_mbid as artist_mbid_api,
  show_data:venue:name::string as venue_name,
  show_data:venue:id::string as venue_id,
  show_data:venue:city:name::string as city_name,
  show_data:venue:city:stateCode::string as state_code,
  show_data:venue:city:country:name::string as country_name,
  show_data:eventDate::string as event_date_str,
  show_data:lastUpdated::string as last_updated,
  current_timestamp() as ingested_at
from flattened_shows
    )
;


  