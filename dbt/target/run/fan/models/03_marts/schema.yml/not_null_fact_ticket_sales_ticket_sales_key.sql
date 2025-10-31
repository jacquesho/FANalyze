
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ticket_sales_key
from DB_T4.FAN_fan_marts.fact_ticket_sales
where ticket_sales_key is null



  
  
      
    ) dbt_internal_test