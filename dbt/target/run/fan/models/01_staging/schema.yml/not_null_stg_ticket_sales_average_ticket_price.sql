
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select average_ticket_price
from DB_T4.FAN_fan_staging.stg_ticket_sales
where average_ticket_price is null



  
  
      
    ) dbt_internal_test