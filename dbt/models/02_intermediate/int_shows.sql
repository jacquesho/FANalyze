{{ config(materialized='table', schema='intermediate') }}

with show_metrics as (
    select
        show_id,
        artist_id,
        artist_name,
        venue_id,
        venue_name,
        show_date,
        city_name,
        state_code,
        country_name,
        market_size,
        venue_type,
        venue_capacity,
        tickets_sold,
        is_sellout,
        attendance_rate,
        average_ticket_price,
        revenue,
        source,

        -- Calculated metrics
        case
            when venue_capacity > 0 then
                round((tickets_sold::float / venue_capacity) * 100, 2)
        end as calculated_attendance_rate,
        tickets_sold >= venue_capacity as calculated_sellout,
        -- Revenue per ticket
        case
            when tickets_sold > 0 then round(revenue / tickets_sold, 2)
        end as revenue_per_ticket,

        -- Date parts for analysis
        extract(year from show_date) as show_year,
        extract(month from show_date) as show_month,
        extract(dayofweek from show_date) as day_of_week,
        extract(quarter from show_date) as show_quarter,

        -- Season
        case
            when extract(month from show_date) in (12, 1, 2) then 'Winter'
            when extract(month from show_date) in (3, 4, 5) then 'Spring'
            when extract(month from show_date) in (6, 7, 8) then 'Summer'
            when extract(month from show_date) in (9, 10, 11) then 'Fall'
        end as season

    from {{ ref('stg_shows_his') }}
)

select * from show_metrics
