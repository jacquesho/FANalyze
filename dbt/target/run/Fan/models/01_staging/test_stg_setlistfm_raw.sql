
  
    

create or replace table DB_T4.FAN_STAGING.test_stg_setlistfm_raw
    
    
    
    as (

-- Simple test model to debug the issue
select 
  'test' as file_name,
  1 as file_row_number,
  '2025-01-01' as fetched_at,
  '1.0' as api_version,
  1 as total_artists,
  1 as total_shows,
  parse_json('{"test": "data"}') as artist_data,
  parse_json('{"test": "payload"}') as raw_payload,
  current_timestamp() as ingested_at
    )
;


  