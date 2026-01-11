{{ config(materialized='table', schema='intermediate') }}

with all_artists as (
    select
        artist_id,
        artist_name,
        artist_tier,
        count(distinct show_id) as total_shows,
        min(show_date) as first_show_date,
        max(show_date) as last_show_date,
        round(avg(attendance_rate), 2) as avg_attendance_rate,
        round(avg(average_ticket_price), 2) as avg_ticket_price,
        round(sum(revenue), 2) as total_revenue,
        sum(tickets_sold) as total_tickets_sold
    from {{ ref('stg_shows_his') }}
    group by artist_id, artist_name, artist_tier
),

future_artists as (
    select
        artist_name,
        count(distinct show_id) as upcoming_shows
    from {{ ref('stg_shows_future') }}
    group by artist_name
)

select
    a.artist_id,
    a.artist_name,
    a.artist_tier,
    a.total_shows,
    a.first_show_date,
    a.last_show_date,
    a.avg_attendance_rate,
    a.avg_ticket_price,
    a.total_revenue,
    a.total_tickets_sold,
    coalesce(f.upcoming_shows, 0) as upcoming_shows,
    coalesce(f.upcoming_shows, 0) > 0 as has_upcoming_shows
from all_artists a
left join future_artists f
    on a.artist_name = f.artist_name
