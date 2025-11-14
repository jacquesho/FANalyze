
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sales_rate
from DB_T4.fan_raw.raw_tickets
where sales_rate is null



  
  
      
    ) dbt_internal_test