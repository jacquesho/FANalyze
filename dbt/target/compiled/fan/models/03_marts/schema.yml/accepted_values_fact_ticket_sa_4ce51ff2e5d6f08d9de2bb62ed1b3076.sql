
    
    

with all_values as (

    select
        demand_category as value_field,
        count(*) as n_records

    from DB_T4.FAN_marts.fact_ticket_sales
    group by demand_category

)

select *
from all_values
where value_field not in (
    'High Demand','Medium Demand','Low Demand','Very Low Demand'
)


