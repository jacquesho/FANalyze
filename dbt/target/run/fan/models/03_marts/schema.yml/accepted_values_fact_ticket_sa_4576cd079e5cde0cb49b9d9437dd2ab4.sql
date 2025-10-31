
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        time_to_show_category as value_field,
        count(*) as n_records

    from DB_T4.FAN_fan_marts.fact_ticket_sales
    group by time_to_show_category

)

select *
from all_values
where value_field not in (
    'Last Week','Last Month','Last Quarter','Future'
)



  
  
      
    ) dbt_internal_test