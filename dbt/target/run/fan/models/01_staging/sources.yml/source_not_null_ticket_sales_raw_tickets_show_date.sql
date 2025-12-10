
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select show_date
from DB_T4.fan_raw.raw_tickets
where show_date is null



  
  
      
    ) dbt_internal_test