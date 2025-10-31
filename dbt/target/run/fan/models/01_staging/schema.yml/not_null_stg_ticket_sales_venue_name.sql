
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select venue_name
from DB_T4.FAN_fan_staging.stg_ticket_sales
where venue_name is null



  
  
      
    ) dbt_internal_test