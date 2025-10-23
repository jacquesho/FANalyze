

-- This model extracts show-level data from the JSONL stage
-- One row per show with basic show information

with jsonl_records as (
  select 
    $1 as raw_json,
    metadata$filename as file_name,
    metadata$file_row_number as file_row_number
  from @FAN_RAW.STAGE_RAW_JSON
)

select
  raw_json:artist_id::string as artist_id,
  raw_json:artist:name::string as artist_name,
  raw_json:show:id::string as show_id,
  to_date(raw_json:show:eventDate::string, 'DD-MM-YYYY') as show_date,
  'setlistfm' as source,
  raw_json:artist:name::string as artist_name_api,
  raw_json:artist:musicbrainz_id::string as artist_mbid_api,
  raw_json:show:venue:name::string as venue_name,
  raw_json:show:venue:id::string as venue_id,
  raw_json:show:venue:city:name::string as city_name,
  raw_json:show:venue:city:stateCode::string as state_code,
  raw_json:show:venue:city:country:name::string as country_name,
  raw_json:show:eventDate::string as event_date_str,
  raw_json:show:lastUpdated::string as last_updated,
  current_timestamp() as ingested_at
from jsonl_records