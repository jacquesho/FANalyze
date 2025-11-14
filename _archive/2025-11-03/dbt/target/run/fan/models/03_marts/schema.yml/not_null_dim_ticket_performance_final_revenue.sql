
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select final_revenue
from DB_T4.FAN_marts.dim_ticket_performance
where final_revenue is null



  
  
      
    ) dbt_internal_test