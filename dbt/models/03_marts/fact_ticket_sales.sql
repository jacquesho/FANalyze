-- Marts layer: Incremental fact table for ticket sales
-- File: models/03_marts/fact_ticket_sales.sql

{{ config(
    materialized='incremental',
    unique_key='ticket_sales_key',
    schema='marts',
    incremental_strategy='merge'
) }}

WITH ticket_sales_staging AS (
    SELECT
        ts.ticket_sales_key,
        ts.id,
        ts.timestamp,
        ts.show_id,
        ts.artist_name,
        ts.venue_name,
        ts.show_date,
        ts.city_name,
        ts.state_code,
        ts.tickets_sold,
        ts.cumulative_tickets_sold,
        ts.revenue,
        ts.cumulative_revenue,
        ts.venue_capacity,
        ts.sales_rate,
        ts.days_until_show,
        ts.artist_tier,
        ts.average_ticket_price,
        ts.venue_utilization_pct,
        ts.sales_velocity_per_day,
        ts.created_at,
        ts.synced_at,

        -- Additional business logic
        CASE
            WHEN ts.sales_rate >= 80 THEN 'High Demand'
            WHEN ts.sales_rate >= 50 THEN 'Medium Demand'
            WHEN ts.sales_rate >= 20 THEN 'Low Demand'
            ELSE 'Very Low Demand'
        END AS demand_category,

        CASE
            WHEN ts.days_until_show <= 7 THEN 'Last Week'
            WHEN ts.days_until_show <= 30 THEN 'Last Month'
            WHEN ts.days_until_show <= 90 THEN 'Last Quarter'
            ELSE 'Future'
        END AS time_to_show_category,

        -- Revenue per ticket calculation
        CASE
            WHEN ts.tickets_sold > 0 THEN
                ROUND(ts.revenue / ts.tickets_sold, 2)
        END AS revenue_per_ticket

    FROM {{ ref('int_ticket_sales_dedup') }} AS ts

    {% if is_incremental() %}
        -- Only process new records since last run (with safe fallback on first load)
        WHERE ts.timestamp >= COALESCE(
            (SELECT MAX(fact.timestamp) FROM {{ this }} AS fact),
            '1970-01-01'::timestamp
        )
    {% endif %}
)

SELECT
    ticket_sales_key,
    id,
    timestamp,
    show_id,
    artist_name,
    venue_name,
    show_date,
    city_name,
    state_code,
    tickets_sold,
    cumulative_tickets_sold,
    revenue,
    cumulative_revenue,
    venue_capacity,
    sales_rate,
    days_until_show,
    artist_tier,
    average_ticket_price,
    venue_utilization_pct,
    sales_velocity_per_day,
    demand_category,
    time_to_show_category,
    revenue_per_ticket,
    created_at,
    synced_at,
    CURRENT_TIMESTAMP() AS dbt_updated_at,
    CURRENT_TIMESTAMP() AS dbt_created_at

FROM ticket_sales_staging
