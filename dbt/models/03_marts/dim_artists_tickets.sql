-- Marts layer: Artist dimension table for ticket sales
-- File: models/03_marts/dim_artists_tickets.sql
-- Built from ticket sales aggregations - independent of batch pipeline

{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH artist_ticket_metrics AS (
    SELECT
        artist_name,
        artist_tier,

        -- Event-level metrics
        COUNT(DISTINCT show_id) AS total_shows_with_sales,
        COUNT(*) AS total_sales_events,

        -- Ticket metrics
        SUM(tickets_sold) AS total_tickets_sold,
        MAX(cumulative_tickets_sold) AS peak_tickets_sold,
        AVG(tickets_sold) AS avg_tickets_per_event,

        -- Revenue metrics
        SUM(revenue) AS total_revenue,
        MAX(cumulative_revenue) AS peak_revenue,
        AVG(revenue) AS avg_revenue_per_event,

        -- Sales velocity metrics
        AVG(sales_velocity_per_day) AS avg_sales_velocity,
        MAX(sales_velocity_per_day) AS peak_sales_velocity,
        MIN(sales_velocity_per_day) AS min_sales_velocity,

        -- Demand analysis
        COUNT(CASE WHEN demand_category = 'High Demand' THEN 1 END) AS high_demand_events,
        COUNT(CASE WHEN demand_category = 'Medium Demand' THEN 1 END) AS medium_demand_events,
        COUNT(CASE WHEN demand_category = 'Low Demand' THEN 1 END) AS low_demand_events,

        -- Time-based patterns
        AVG(days_until_show) AS avg_days_until_show,
        MIN(days_until_show) AS min_days_until_show,
        MAX(days_until_show) AS max_days_until_show,

        -- Pricing metrics
        AVG(average_ticket_price) AS avg_ticket_price,
        MIN(average_ticket_price) AS min_ticket_price,
        MAX(average_ticket_price) AS max_ticket_price,

        -- Date range
        MIN(timestamp) AS first_sale_timestamp,
        MAX(timestamp) AS last_sale_timestamp,
        MIN(show_date) AS earliest_show_date,
        MAX(show_date) AS latest_show_date

    FROM {{ ref('fact_ticket_sales') }}
    GROUP BY artist_name, artist_tier
)

SELECT
    artist_name,
    artist_tier,

    -- Core metrics
    total_shows_with_sales,
    total_sales_events,
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

    -- Sales velocity metrics
    ROUND(avg_sales_velocity, 2) AS avg_sales_velocity,
    ROUND(peak_sales_velocity, 2) AS peak_sales_velocity,
    ROUND(min_sales_velocity, 2) AS min_sales_velocity,

    -- Demand distribution
    high_demand_events,
    medium_demand_events,
    low_demand_events,
    CASE
        WHEN total_sales_events > 0 THEN
            ROUND((high_demand_events::FLOAT / total_sales_events::FLOAT) * 100, 2)
    END AS high_demand_pct,

    -- Time patterns
    ROUND(avg_days_until_show, 0) AS avg_days_until_show,
    min_days_until_show,
    max_days_until_show,

    -- Pricing range
    ROUND(avg_ticket_price, 2) AS avg_ticket_price,
    ROUND(min_ticket_price, 2) AS min_ticket_price,
    ROUND(max_ticket_price, 2) AS max_ticket_price,

    -- Date range
    first_sale_timestamp,
    last_sale_timestamp,
    earliest_show_date,
    latest_show_date,

    -- Performance classification
    CASE
        WHEN avg_sales_velocity >= 10 THEN 'High Velocity'
        WHEN avg_sales_velocity >= 5 THEN 'Medium Velocity'
        WHEN avg_sales_velocity >= 2 THEN 'Low Velocity'
        ELSE 'Very Low Velocity'
    END AS sales_velocity_tier,

    CASE
        WHEN total_revenue >= 1000000 THEN 'High Revenue'
        WHEN total_revenue >= 500000 THEN 'Medium Revenue'
        WHEN total_revenue >= 100000 THEN 'Low Revenue'
        ELSE 'Very Low Revenue'
    END AS revenue_tier,

    CURRENT_TIMESTAMP AS dbt_updated_at,
    CURRENT_TIMESTAMP AS dbt_created_at

FROM artist_ticket_metrics
