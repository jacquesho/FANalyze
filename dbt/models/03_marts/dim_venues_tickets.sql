-- Marts layer: Venue dimension table for ticket sales
-- File: models/03_marts/dim_venues_tickets.sql
-- Built from ticket sales aggregations - independent of batch pipeline

{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH venue_ticket_metrics AS (
    SELECT
        venue_name,
        city_name,
        state_code,
        MAX(venue_capacity) AS venue_capacity,  -- Should be consistent per venue

        -- Show-level metrics
        COUNT(DISTINCT show_id) AS total_shows,
        COUNT(DISTINCT artist_name) AS unique_artists,

        -- Event-level metrics
        COUNT(*) AS total_sales_events,

        -- Ticket metrics
        SUM(tickets_sold) AS total_tickets_sold,
        MAX(cumulative_tickets_sold) AS peak_tickets_sold,
        AVG(tickets_sold) AS avg_tickets_per_event,

        -- Revenue metrics
        SUM(revenue) AS total_revenue,
        MAX(cumulative_revenue) AS peak_revenue,
        AVG(revenue) AS avg_revenue_per_event,

        -- Utilization metrics
        AVG(venue_utilization_pct) AS avg_utilization_pct,
        MAX(venue_utilization_pct) AS peak_utilization_pct,
        MIN(venue_utilization_pct) AS min_utilization_pct,

        -- Sales rate metrics
        AVG(sales_rate) AS avg_sales_rate,
        MAX(sales_rate) AS peak_sales_rate,

        -- Sales velocity
        AVG(sales_velocity_per_day) AS avg_sales_velocity,
        MAX(sales_velocity_per_day) AS peak_sales_velocity,

        -- Demand analysis
        COUNT(CASE WHEN demand_category = 'High Demand' THEN 1 END) AS high_demand_events,
        COUNT(CASE WHEN sales_rate >= 80 THEN 1 END) AS near_sellout_events,

        -- Pricing metrics
        AVG(average_ticket_price) AS avg_ticket_price,

        -- Date range
        MIN(timestamp) AS first_sale_timestamp,
        MAX(timestamp) AS last_sale_timestamp,
        MIN(show_date) AS earliest_show_date,
        MAX(show_date) AS latest_show_date

    FROM {{ ref('fact_ticket_sales') }}
    GROUP BY venue_name, city_name, state_code
)

SELECT
    venue_name,
    city_name,
    state_code,
    venue_capacity,

    -- Show metrics
    total_shows,
    unique_artists,
    CASE
        WHEN total_shows > 0 THEN ROUND(unique_artists::FLOAT / total_shows::FLOAT, 2)
    END AS artists_per_show_ratio,

    -- Event metrics
    total_sales_events,
    CASE
        WHEN total_shows > 0 THEN ROUND(total_sales_events::FLOAT / total_shows::FLOAT, 0)
    END AS avg_events_per_show,

    -- Ticket metrics
    total_tickets_sold,
    peak_tickets_sold,
    avg_tickets_per_event,

    -- Revenue metrics
    total_revenue,
    peak_revenue,
    avg_revenue_per_event,
    CASE
        WHEN total_tickets_sold > 0 THEN ROUND(total_revenue / total_tickets_sold, 2)
    END AS avg_revenue_per_ticket,

    -- Utilization metrics
    ROUND(avg_utilization_pct, 2) AS avg_utilization_pct,
    ROUND(peak_utilization_pct, 2) AS peak_utilization_pct,
    ROUND(min_utilization_pct, 2) AS min_utilization_pct,

    -- Sales rate metrics
    ROUND(avg_sales_rate, 2) AS avg_sales_rate,
    ROUND(peak_sales_rate, 2) AS peak_sales_rate,

    -- Sales velocity
    ROUND(avg_sales_velocity, 2) AS avg_sales_velocity,
    ROUND(peak_sales_velocity, 2) AS peak_sales_velocity,

    -- Demand metrics
    high_demand_events,
    near_sellout_events,
    CASE
        WHEN total_sales_events > 0 THEN
            ROUND((near_sellout_events::FLOAT / total_sales_events::FLOAT) * 100, 2)
    END AS sellout_rate_pct,

    -- Pricing
    ROUND(avg_ticket_price, 2) AS avg_ticket_price,

    -- Date range
    first_sale_timestamp,
    last_sale_timestamp,
    earliest_show_date,
    latest_show_date,

    -- Venue size classification
    CASE
        WHEN venue_capacity >= 50000 THEN 'Stadium'
        WHEN venue_capacity >= 20000 THEN 'Arena'
        WHEN venue_capacity >= 5000 THEN 'Large Theater'
        WHEN venue_capacity >= 1000 THEN 'Theater'
        ELSE 'Small Venue'
    END AS venue_size_class,

    -- Performance classification
    CASE
        WHEN avg_utilization_pct >= 80 THEN 'High Performance'
        WHEN avg_utilization_pct >= 60 THEN 'Good Performance'
        WHEN avg_utilization_pct >= 40 THEN 'Average Performance'
        ELSE 'Low Performance'
    END AS performance_tier,

    -- Sales pattern classification
    CASE
        WHEN avg_sales_velocity >= 8 AND sellout_rate_pct >= 30 THEN 'High Demand Venue'
        WHEN avg_sales_velocity >= 5 THEN 'Steady Sales Venue'
        WHEN avg_sales_velocity >= 2 THEN 'Slow Sales Venue'
        ELSE 'Low Demand Venue'
    END AS sales_pattern_type,

    CURRENT_TIMESTAMP() AS dbt_updated_at,
    CURRENT_TIMESTAMP() AS dbt_created_at

FROM venue_ticket_metrics
