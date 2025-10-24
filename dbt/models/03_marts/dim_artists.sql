{{ config(materialized='table', schema='marts') }}

select 
    artist_id,
    artist_name,
    artist_tier,
    total_shows,
    first_show_date,
    last_show_date,
    avg_attendance_rate,
    avg_ticket_price,
    total_revenue,
    total_tickets_sold,
    upcoming_shows,
    has_upcoming_shows,
    
    -- Performance metrics
    case 
        when total_shows > 0 then round(total_revenue / total_shows, 2)
        else 0
    end as avg_revenue_per_show,
    
    case 
        when total_shows > 0 then round(total_tickets_sold / total_shows, 0)
        else 0
    end as avg_tickets_per_show,
    
    -- Tier classification
    case 
        when artist_tier = 'A-list' then 'Tier 1'
        when artist_tier = 'B-list' then 'Tier 2'
        when artist_tier = 'C-list' then 'Tier 3'
        else 'Unknown'
    end as tier_classification,
    
    -- Activity status
    case 
        when last_show_date >= current_date - interval '1 year' then 'Active'
        when last_show_date >= current_date - interval '2 years' then 'Recently Active'
        else 'Inactive'
    end as activity_status
    
from {{ ref('int_artists') }}
