
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        performance_rating as value_field,
        count(*) as n_records

    from DB_T4.FAN_marts.dim_ticket_performance
    group by performance_rating

)

select *
from all_values
where value_field not in (
    'Excellent','Good','Average','Below Average','Poor'
)



  
  
      
    ) dbt_internal_test