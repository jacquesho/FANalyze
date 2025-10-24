
  
    

create or replace transient table DB_T4.FAN_intermediate.int_artists
    
    
    
    as (

with all_artists as (
    select distinct
        artist_id,
        artist_name,
        artist_tier,
        count(distinct show_id) as total_shows,
        min(show_date) as first_show_date,
        max(show_date) as last_show_date,
        avg(attendance_rate) as avg_attendance_rate,
        avg(average_ticket_price) as avg_ticket_price,
        sum(revenue) as total_revenue,
        sum(tickets_sold) as total_tickets_sold
    from DB_T4.FAN_staging.stg_shows_his
    group by artist_id, artist_name, artist_tier
),

future_artists as (
    select distinct
        artist_name,
        count(distinct show_id) as upcoming_shows
    from DB_T4.FAN_staging.stg_shows_future
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
    case 
        when f.upcoming_shows > 0 then true 
        else false 
    end as has_upcoming_shows
from all_artists a
left join future_artists f on a.artist_name = f.artist_name
    )
;


  