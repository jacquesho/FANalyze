
  
    

create or replace table DB_T4.FAN_STAGING.stg_test
    
    
    
    as (

-- Ultra-simple test to see if we can get any data from the stage

select
  $1 as raw_data,
  metadata$filename as file_name,
  metadata$file_row_number as row_number
from @FAN_RAW.STAGE_RAW_JSON
    )
;


  