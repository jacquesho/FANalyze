
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_tickets_sold
from DB_T4.FAN_marts.mart_ticket_performance
where total_tickets_sold is null



  
  
      
    ) dbt_internal_test