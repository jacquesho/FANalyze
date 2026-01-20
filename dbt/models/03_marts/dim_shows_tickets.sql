-- Marts layer: Show dimension table for ticket sales
-- File: models/03_marts/dim_shows_tickets.sql
-- Show-level dimension built from ticket sales final metrics

{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH show_final_metrics AS (
    SELECT
        show_id,
        artist_name,
        venue_name,
        show_date,
        city_name,
        state_code,
        artist_tier,
        MAX(venue_capacity) AS venue_capacity,  -- Should be consistent per show

        -- Final sales metrics (from last event per show)
        MAX(cumulative_tickets_sold) AS final_tickets_sold,
        MAX(cumulative_revenue) AS final_revenue,
        MAX(sales_rate) AS final_sales_rate,
        MAX(venue_utilization_pct) AS final_utilization_pct,

        -- Event metrics
        COUNT(*) AS total_sales_events,
        SUM(tickets_sold) AS total_tickets_sold_events,
        SUM(revenue) AS total_revenue_events,

        -- Sales velocity metrics
        AVG(sales_velocity_per_day) AS avg_sales_velocity,
        MAX(sales_velocity_per_day) AS peak_sales_velocity,

        -- Time metrics
        MAX(days_until_show) AS days_until_show,
        MIN(days_until_show) AS min_days_until_show_at_sale,

        -- Pricing metrics
        AVG(average_ticket_price) AS avg_ticket_price,
        MIN(average_ticket_price) AS min_ticket_price,
        MAX(average_ticket_price) AS max_ticket_price,

        -- Demand patterns
        MAX(CASE WHEN demand_category = 'High Demand' THEN 1 ELSE 0 END) AS reached_high_demand,
        MAX(CASE WHEN demand_category = 'Medium Demand' THEN 1 ELSE 0 END) AS reached_medium_demand,

        -- Time-based categories
        MAX(CASE WHEN time_to_show_category = 'Last Week' THEN 1 ELSE 0 END) AS had_last_week_sales,
        MAX(
            CASE WHEN time_to_show_category = 'Last Month' THEN 1 ELSE 0 END
        ) AS had_last_month_sales,

        -- Date range
        MIN(timestamp) AS first_sale_timestamp,
        MAX(timestamp) AS last_sale_timestamp,
        DATEDIFF(DAY, MIN(timestamp), MAX(timestamp)) AS sales_period_days

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
    venue_capacity,

    -- Final sales metrics
    final_tickets_sold,
    final_revenue,
    ROUND(final_sales_rate, 2) AS final_sales_rate,
    ROUND(final_utilization_pct, 2) AS final_utilization_pct,

    -- Event metrics
    total_sales_events,
    total_tickets_sold_events,
    total_revenue_events,

    -- Sales velocity
    ROUND(avg_sales_velocity, 2) AS avg_sales_velocity,
    ROUND(peak_sales_velocity, 2) AS peak_sales_velocity,

    -- Time metrics
    days_until_show,
    min_days_until_show_at_sale,
    sales_period_days,

    -- Pricing
    ROUND(avg_ticket_price, 2) AS avg_ticket_price,
    ROUND(min_ticket_price, 2) AS min_ticket_price,
    ROUND(max_ticket_price, 2) AS max_ticket_price,

    -- Demand indicators
    reached_high_demand,
    reached_medium_demand,
    had_last_week_sales,
    had_last_month_sales,

    -- Date range
    first_sale_timestamp,
    last_sale_timestamp,

    -- Calculated metrics
    CASE
        WHEN venue_capacity > 0 THEN
            ROUND((final_tickets_sold::FLOAT / venue_capacity::FLOAT) * 100, 2)
    END AS calculated_utilization_pct,

    CASE
        WHEN final_tickets_sold > 0 THEN
            ROUND(final_revenue / final_tickets_sold, 2)
    END AS final_revenue_per_ticket,

    -- Show status
    CASE
        WHEN show_date < CURRENT_DATE THEN 'Past'
        WHEN show_date = CURRENT_DATE THEN 'Today'
        WHEN show_date <= DATEADD(DAY, 7, CURRENT_DATE) THEN 'This Week'
        WHEN show_date <= DATEADD(DAY, 30, CURRENT_DATE) THEN 'This Month'
        ELSE 'Future'
    END AS show_status,

    -- Performance rating
    CASE
        WHEN final_sales_rate >= 90 AND avg_sales_velocity >= 8 THEN 'Excellent'
        WHEN final_sales_rate >= 70 AND avg_sales_velocity >= 5 THEN 'Good'
        WHEN final_sales_rate >= 50 THEN 'Average'
        WHEN final_sales_rate >= 30 THEN 'Below Average'
        ELSE 'Poor'
    END AS performance_rating,

    -- Demand category
    CASE
        WHEN final_sales_rate >= 80 THEN 'High Demand'
        WHEN final_sales_rate >= 50 THEN 'Medium Demand'
        WHEN final_sales_rate >= 20 THEN 'Low Demand'
        ELSE 'Very Low Demand'
    END AS final_demand_category,

    -- Sellout status
    CASE
        WHEN final_tickets_sold >= venue_capacity THEN 'Sold Out'
        WHEN final_sales_rate >= 90 THEN 'Near Sellout'
        WHEN final_sales_rate >= 70 THEN 'High Sales'
        WHEN final_sales_rate >= 50 THEN 'Moderate Sales'
        ELSE 'Low Sales'
    END AS sellout_status,

    CURRENT_TIMESTAMP AS dbt_updated_at,
    CURRENT_TIMESTAMP AS dbt_created_at

FROM show_final_metrics
