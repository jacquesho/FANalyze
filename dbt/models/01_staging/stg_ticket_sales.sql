-- Staging layer: Clean and standardize ticket sales data
-- File: models/02_staging/stg_ticket_sales.sql

{{ config(
    materialized='table',
    schema='STAGING'
) }}

with cleaned_ticket_sales as (
    select
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
        synced_at,

        -- Data quality checks
        case
            when tickets_sold < 0 then null
            else tickets_sold
        end as tickets_sold_clean,
        case
            when revenue < 0 then null
            else revenue
        end as revenue_clean,
        case
            when venue_capacity <= 0 then null
            else venue_capacity
        end as venue_capacity_clean,

        -- Generate unique key using custom macro
        {{ generate_ticket_sales_key('show_id', 'timestamp') }} as ticket_sales_key

    from {{ source('ticket_sales', 'raw_tickets') }}
    where
        -- Filter out invalid records
        show_id is not null
        and artist_name is not null
        and venue_name is not null
        and show_date is not null
        and timestamp is not null
)

select
    id,
    timestamp,
    show_id,
    artist_name,
    venue_name,
    show_date,
    city_name,
    state_code,
    tickets_sold_clean as tickets_sold,
    cumulative_tickets_sold,
    revenue_clean as revenue,
    cumulative_revenue,
    venue_capacity_clean as venue_capacity,
    sales_rate,
    days_until_show,
    artist_tier,
    average_ticket_price,
    created_at,
    synced_at,
    ticket_sales_key,

    -- Additional calculated fields
    case
        when venue_capacity_clean > 0 then
            round(
                (cumulative_tickets_sold::float / venue_capacity_clean::float) * 100,
                2
            )
    end as venue_utilization_pct,

    -- Sales velocity calculation using custom macro
    {{
        calculate_sales_velocity('tickets_sold_clean', 'days_until_show')
    }} as sales_velocity_per_day

from cleaned_ticket_sales
