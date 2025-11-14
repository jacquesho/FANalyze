
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select venue_capacity
from DB_T4.fan_raw.raw_tickets
where venue_capacity is null



  
  
      
    ) dbt_internal_test