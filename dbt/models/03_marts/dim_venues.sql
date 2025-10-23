{{ config(materialized='table') }}

select 
    venue_id,
    venue_name,
    venue_type,
    venue_capacity,
    city_name,
    state_code,
    country_name,
    market_size,
    total_shows,
    unique_artists,
    avg_attendance_rate,
    avg_ticket_price,
    total_revenue,
    total_tickets_sold,
    sellout_count,
    sellout_rate,
    first_show_date,
    last_show_date,
    upcoming_shows,
    has_upcoming_shows,
    
    -- Venue performance metrics
    case 
        when total_shows > 0 then round(total_revenue / total_shows, 2)
        else 0
    end as avg_revenue_per_show,
    
    case 
        when total_shows > 0 then round(total_tickets_sold / total_shows, 0)
        else 0
    end as avg_tickets_per_show,
    
    -- Venue size classification
    case 
        when venue_capacity >= 50000 then 'Stadium'
        when venue_capacity >= 20000 then 'Arena'
        when venue_capacity >= 5000 then 'Large Theater'
        when venue_capacity >= 1000 then 'Theater'
        else 'Small Venue'
    end as venue_size_class,
    
    -- Market performance
    case 
        when avg_attendance_rate >= 90 then 'High Performance'
        when avg_attendance_rate >= 70 then 'Good Performance'
        when avg_attendance_rate >= 50 then 'Average Performance'
        else 'Low Performance'
    end as performance_tier
    
from {{ ref('int_venues') }}
