
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select average_ticket_price
from DB_T4.fan_raw.raw_tickets
where average_ticket_price is null



  
  
      
    ) dbt_internal_test