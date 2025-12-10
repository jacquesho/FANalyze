
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select daily_tickets_sold
from DB_T4.FAN_marts.mart_daily_ticket_summary
where daily_tickets_sold is null



  
  
      
    ) dbt_internal_test