-- Marts layer: Daily aggregated ticket sales summary
-- File: models/03_marts/mart_daily_ticket_summary.sql



WITH daily_ticket_metrics AS (
    SELECT 
        DATE(timestamp) AS sale_date,
        artist_name,
        city_name,
        state_code,
        artist_tier,
        
        -- Daily aggregates
        COUNT(*) AS daily_sales_events,
        COUNT(DISTINCT show_id) AS shows_with_sales,
        SUM(tickets_sold) AS daily_tickets_sold,
        SUM(revenue) AS daily_revenue,
        
        -- Performance metrics
        AVG(sales_rate) AS avg_daily_sales_rate,
        AVG(venue_utilization_pct) AS avg_daily_venue_utilization,
        AVG(sales_velocity_per_day) AS avg_daily_sales_velocity,
        
        -- Revenue metrics
        CASE 
            WHEN SUM(tickets_sold) > 0 THEN ROUND(SUM(revenue) / SUM(tickets_sold), 2)
            ELSE NULL 
        END AS avg_daily_revenue_per_ticket,
        
        -- Demand analysis
        SUM(CASE WHEN demand_category = 'High Demand' THEN 1 ELSE 0 END) AS high_demand_events,
        SUM(CASE WHEN demand_category = 'Medium Demand' THEN 1 ELSE 0 END) AS medium_demand_events,
        SUM(CASE WHEN demand_category = 'Low Demand' THEN 1 ELSE 0 END) AS low_demand_events,
        
        -- Time analysis
        AVG(days_until_show) AS avg_days_until_show,
        MIN(days_until_show) AS min_days_until_show,
        MAX(days_until_show) AS max_days_until_show
        
    FROM DB_T4.FAN_marts.fact_ticket_sales
    GROUP BY 
        DATE(timestamp), artist_name, city_name, state_code, artist_tier
)

SELECT 
    sale_date,
    artist_name,
    city_name,
    state_code,
    artist_tier,
    
    -- Core daily metrics
    daily_sales_events,
    shows_with_sales,
    daily_tickets_sold,
    daily_revenue,
    
    -- Performance metrics
    ROUND(avg_daily_sales_rate, 2) AS avg_daily_sales_rate,
    ROUND(avg_daily_venue_utilization, 2) AS avg_daily_venue_utilization,
    ROUND(avg_daily_sales_velocity, 2) AS avg_daily_sales_velocity,
    avg_daily_revenue_per_ticket,
    
        -- Demand distribution
        high_demand_events,
        medium_demand_events,
        low_demand_events,
    
    -- Demand percentage
    ROUND((high_demand_events::FLOAT / daily_sales_events::FLOAT) * 100, 2) AS high_demand_pct,
    ROUND((medium_demand_events::FLOAT / daily_sales_events::FLOAT) * 100, 2) AS medium_demand_pct,
    ROUND((low_demand_events::FLOAT / daily_sales_events::FLOAT) * 100, 2) AS low_demand_pct,
    
    -- Time metrics
    ROUND(avg_days_until_show, 1) AS avg_days_until_show,
    min_days_until_show,
    max_days_until_show,
    
    -- Daily performance rating
    CASE 
        WHEN avg_daily_sales_rate >= 70 AND avg_daily_sales_velocity >= 8 THEN 'Excellent Day'
        WHEN avg_daily_sales_rate >= 50 AND avg_daily_sales_velocity >= 5 THEN 'Good Day'
        WHEN avg_daily_sales_rate >= 30 AND avg_daily_sales_velocity >= 2 THEN 'Average Day'
        WHEN avg_daily_sales_rate >= 15 THEN 'Below Average Day'
        ELSE 'Poor Day'
    END AS daily_performance_rating,
    
    -- Revenue tier
    CASE 
        WHEN daily_revenue >= 10000 THEN 'High Revenue'
        WHEN daily_revenue >= 5000 THEN 'Medium Revenue'
        WHEN daily_revenue >= 1000 THEN 'Low Revenue'
        ELSE 'Very Low Revenue'
    END AS daily_revenue_tier,
    
    CURRENT_TIMESTAMP() AS dbt_created_at
    
FROM daily_ticket_metrics
ORDER BY sale_date DESC, daily_revenue DESC