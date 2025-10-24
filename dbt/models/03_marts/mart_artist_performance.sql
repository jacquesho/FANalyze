{{ config(materialized='table', schema='marts') }}

with artist_metrics as (
    select 
        a.artist_id,
        a.artist_name,
        a.artist_tier,
        a.total_shows,
        a.avg_attendance_rate,
        a.avg_ticket_price,
        a.total_revenue,
        a.total_tickets_sold,
        a.upcoming_shows,
        
        -- Performance rankings
        rank() over (order by a.total_revenue desc) as revenue_rank,
        rank() over (order by a.total_tickets_sold desc) as tickets_rank,
        rank() over (order by a.avg_attendance_rate desc) as attendance_rank,
        
        -- Market share
        sum(a.total_revenue) over () as total_market_revenue,
        round((a.total_revenue / sum(a.total_revenue) over ()) * 100, 2) as revenue_market_share,
        
        sum(a.total_tickets_sold) over () as total_market_tickets,
        round((a.total_tickets_sold / sum(a.total_tickets_sold) over ()) * 100, 2) as tickets_market_share
        
    from {{ ref('dim_artists') }} a
),

venue_diversity as (
    select 
        artist_id,
        count(distinct venue_id) as unique_venues,
        count(distinct city_name) as unique_cities,
        count(distinct state_code) as unique_states
    from {{ ref('fact_shows') }}
    group by artist_id
)

select 
    am.artist_id,
    am.artist_name,
    am.artist_tier,
    am.total_shows,
    am.avg_attendance_rate,
    am.avg_ticket_price,
    am.total_revenue,
    am.total_tickets_sold,
    am.upcoming_shows,
    am.revenue_rank,
    am.tickets_rank,
    am.attendance_rank,
    am.revenue_market_share,
    am.tickets_market_share,
    
    -- Diversity metrics
    vd.unique_venues,
    vd.unique_cities,
    vd.unique_states,
    
    -- Performance categories
    case 
        when am.revenue_rank <= 5 then 'Top Performer'
        when am.revenue_rank <= 20 then 'High Performer'
        when am.revenue_rank <= 50 then 'Medium Performer'
        else 'Low Performer'
    end as performance_category,
    
    -- Growth potential
    case 
        when am.upcoming_shows > am.total_shows * 0.1 then 'High Growth'
        when am.upcoming_shows > 0 then 'Moderate Growth'
        else 'No Growth'
    end as growth_potential
    
from artist_metrics am
left join venue_diversity vd on am.artist_id = vd.artist_id
