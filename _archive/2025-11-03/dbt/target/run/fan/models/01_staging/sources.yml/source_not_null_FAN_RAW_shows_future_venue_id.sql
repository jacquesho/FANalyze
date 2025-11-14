
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select venue_id
from DB_T4.FAN_RAW.shows_future
where venue_id is null



  
  
      
    ) dbt_internal_test