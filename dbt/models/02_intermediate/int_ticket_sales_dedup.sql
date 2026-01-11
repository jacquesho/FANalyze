-- Intermediate layer: Deduplicate ticket sales by natural key
-- Keeps latest record per ticket_sales_key by timestamp
-- File: models/02_intermediate/int_ticket_sales_dedup.sql

{{ config(
    materialized='table',
    schema='intermediate'
) }}

WITH ranked AS (
    SELECT
        ts.*,
        ROW_NUMBER() OVER (
            PARTITION BY ts.ticket_sales_key
            ORDER BY ts.timestamp DESC, ts.created_at DESC, ts.id DESC
        ) AS rn
    FROM {{ ref('stg_ticket_sales') }} AS ts
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
    created_at,
    synced_at
FROM ranked
WHERE rn = 1
