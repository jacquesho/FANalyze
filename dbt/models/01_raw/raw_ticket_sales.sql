-- Raw layer: Source definition for streaming ticket data
-- File: models/01_raw/raw_ticket_sales.sql

{{ config(
    materialized='table',
    schema='fan_raw'
) }}

SELECT 
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
    created_at,
    synced_at
FROM {{ source('ticket_sales', 'raw_tickets') }}
