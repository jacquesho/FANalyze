{{ config(materialized='table', schema='intermediate') }}

with venue_performance as (
    select 
        venue_id,
        venue_name,
        venue_type,
        max(venue_capacity) as venue_capacity,
        city_name,
        state_code,
        country_name,
        market_size,
        count(distinct show_id) as total_shows,
        count(distinct artist_id) as unique_artists,
        round(avg(attendance_rate), 2) as avg_attendance_rate,
        round(avg(average_ticket_price), 2) as avg_ticket_price,
        round(sum(revenue), 2) as total_revenue,
        sum(tickets_sold) as total_tickets_sold,
        sum(case when is_sellout then 1 else 0 end) as sellout_count,
        min(show_date) as first_show_date,
        max(show_date) as last_show_date
    from {{ ref('stg_shows_his') }}
    group by venue_id, venue_name, venue_type, city_name, state_code, country_name, market_size
),

upcoming_venues as (
    select 
        venue_id,
        venue_name,
        count(distinct show_id) as upcoming_shows
    from {{ ref('stg_shows_future') }}
    group by venue_id, venue_name
)

select 
    v.venue_id,
    v.venue_name,
    v.venue_type,
    v.venue_capacity,
    v.city_name,
    v.state_code,
    v.country_name,
    v.market_size,
    v.total_shows,
    v.unique_artists,
    v.avg_attendance_rate,
    v.avg_ticket_price,
    v.total_revenue,
    v.total_tickets_sold,
    v.sellout_count,
    round((v.sellout_count::float / v.total_shows) * 100, 2) as sellout_rate,
    v.first_show_date,
    v.last_show_date,
    coalesce(u.upcoming_shows, 0) as upcoming_shows,
    case 
        when u.upcoming_shows > 0 then true 
        else false 
    end as has_upcoming_shows
from venue_performance v
left join upcoming_venues u on v.venue_id = u.venue_id
