
    
    

with all_values as (

    select
        daily_performance_rating as value_field,
        count(*) as n_records

    from DB_T4.FAN_marts.mart_daily_ticket_summary
    group by daily_performance_rating

)

select *
from all_values
where value_field not in (
    'Excellent Day','Good Day','Average Day','Below Average Day','Poor Day'
)


