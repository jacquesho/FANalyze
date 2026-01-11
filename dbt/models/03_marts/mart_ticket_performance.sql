-- Marts layer: Dimension table for ticket performance metrics
-- File: models/03_marts/mart_ticket_performance.sql

{{ config(
    materialized='table',
    schema='marts'
) }}

WITH show_performance AS (
    SELECT
        show_id,
        artist_name,
        venue_name,
        show_date,
        city_name,
        state_code,
        artist_tier,

        -- Aggregate metrics per show
        COUNT(*) AS total_sales_events,
        SUM(tickets_sold) AS total_tickets_sold,
        MAX(cumulative_tickets_sold) AS final_tickets_sold,
        SUM(revenue) AS total_revenue,
        MAX(cumulative_revenue) AS final_revenue,
        MAX(venue_capacity) AS venue_capacity,
        MAX(sales_rate) AS final_sales_rate,
        MAX(venue_utilization_pct) AS final_venue_utilization,

        -- Time-based metrics
        MIN(timestamp) AS first_sale_timestamp,
        MAX(timestamp) AS last_sale_timestamp,
        MAX(days_until_show) AS days_until_show,

        -- Performance calculations using custom macro
        {{
            calculate_sales_velocity(
                'SUM(tickets_sold)', 'MAX(days_until_show)'
            )
        }} AS overall_sales_velocity,

        -- Demand analysis
        MAX(CASE WHEN demand_category = 'High Demand' THEN 1 ELSE 0 END) AS had_high_demand,
        MAX(CASE WHEN demand_category = 'Medium Demand' THEN 1 ELSE 0 END) AS had_medium_demand,

        -- Revenue metrics
        CASE
            WHEN SUM(tickets_sold) > 0 THEN
                ROUND(SUM(revenue) / SUM(tickets_sold), 2)
        END AS avg_revenue_per_ticket

    FROM {{ ref('fact_ticket_sales') }}
    GROUP BY
        show_id, artist_name, venue_name, show_date,
        city_name, state_code, artist_tier
)

SELECT
    show_id,
    artist_name,
    venue_name,
    show_date,
    city_name,
    state_code,
    artist_tier,

    -- Core metrics
    total_sales_events,
    total_tickets_sold,
    final_tickets_sold,
    total_revenue,
    final_revenue,
    venue_capacity,
    final_sales_rate,
    final_venue_utilization,

    -- Time metrics
    first_sale_timestamp,
    last_sale_timestamp,
    days_until_show,
    overall_sales_velocity,

    -- Performance indicators
    had_high_demand,
    had_medium_demand,
    avg_revenue_per_ticket,

    -- Calculated performance score
    CASE
        WHEN final_sales_rate >= 80 AND overall_sales_velocity >= 10 THEN 'Excellent'
        WHEN final_sales_rate >= 60 AND overall_sales_velocity >= 5 THEN 'Good'
        WHEN final_sales_rate >= 40 AND overall_sales_velocity >= 2 THEN 'Average'
        WHEN final_sales_rate >= 20 THEN 'Below Average'
        ELSE 'Poor'
    END AS performance_rating,

    -- Capacity utilization category
    CASE
        WHEN final_venue_utilization >= 90 THEN 'Sold Out'
        WHEN final_venue_utilization >= 75 THEN 'Near Capacity'
        WHEN final_venue_utilization >= 50 THEN 'Half Full'
        WHEN final_venue_utilization >= 25 THEN 'Quarter Full'
        ELSE 'Low Attendance'
    END AS capacity_category,

    CURRENT_TIMESTAMP() AS dbt_created_at

FROM show_performance
ORDER BY show_date DESC, final_revenue DESC

