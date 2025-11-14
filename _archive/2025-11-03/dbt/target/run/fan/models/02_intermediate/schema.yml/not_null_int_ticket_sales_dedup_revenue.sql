
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select revenue
from DB_T4.FAN_intermediate.int_ticket_sales_dedup
where revenue is null



  
  
      
    ) dbt_internal_test