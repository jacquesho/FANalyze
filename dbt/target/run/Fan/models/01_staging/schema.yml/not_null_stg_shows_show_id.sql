
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select show_id
from DB_T4.FAN_STAGING.stg_shows
where show_id is null



  
  
      
    ) dbt_internal_test