
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sales_rate
from DB_T4.FAN_staging.stg_ticket_sales
where sales_rate is null



  
  
      
    ) dbt_internal_test