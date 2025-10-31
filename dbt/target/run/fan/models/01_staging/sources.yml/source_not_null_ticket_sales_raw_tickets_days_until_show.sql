
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select days_until_show
from DB_T4.fan_raw.raw_tickets
where days_until_show is null



  
  
      
    ) dbt_internal_test