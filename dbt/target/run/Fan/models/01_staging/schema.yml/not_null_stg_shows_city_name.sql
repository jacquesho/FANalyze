
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select city_name
from DB_T4.FAN_STAGING.stg_shows
where city_name is null



  
  
      
    ) dbt_internal_test