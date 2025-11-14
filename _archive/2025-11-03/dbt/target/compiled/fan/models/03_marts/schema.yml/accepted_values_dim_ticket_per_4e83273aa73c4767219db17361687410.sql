
    
    

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


