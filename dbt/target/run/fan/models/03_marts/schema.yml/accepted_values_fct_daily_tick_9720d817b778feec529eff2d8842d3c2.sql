
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        daily_revenue_tier as value_field,
        count(*) as n_records

    from DB_T4.FAN_marts.fct_daily_ticket_summary
    group by daily_revenue_tier

)

select *
from all_values
where value_field not in (
    'High Revenue','Medium Revenue','Low Revenue','Very Low Revenue'
)



  
  
      
    ) dbt_internal_test