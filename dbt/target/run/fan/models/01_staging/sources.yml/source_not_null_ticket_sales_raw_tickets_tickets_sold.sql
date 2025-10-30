
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select tickets_sold
from DB_T4.fan_raw.raw_tickets
where tickets_sold is null



  
  
      
    ) dbt_internal_test