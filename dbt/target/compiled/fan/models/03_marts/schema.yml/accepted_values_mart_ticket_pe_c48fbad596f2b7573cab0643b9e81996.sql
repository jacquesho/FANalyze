
    
    

with all_values as (

    select
        capacity_category as value_field,
        count(*) as n_records

    from DB_T4.FAN_marts.mart_ticket_performance
    group by capacity_category

)

select *
from all_values
where value_field not in (
    'Sold Out','Near Capacity','Half Full','Quarter Full','Low Attendance'
)


