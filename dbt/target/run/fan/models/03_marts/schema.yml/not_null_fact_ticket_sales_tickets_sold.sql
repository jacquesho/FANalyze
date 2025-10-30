
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select tickets_sold
from DB_T4.FAN_fan_marts.fact_ticket_sales
where tickets_sold is null



  
  
      
    ) dbt_internal_test