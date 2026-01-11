{{ config(materialized='view', schema='staging') }}

with source_data as (
    select * from {{ source('FAN_RAW', 'shows_his') }}
),

cleaned_data as (
    select
        -- Identifiers
        artist_id,
        artist_name,
        show_id,
        venue_id,
        venue_name,

        -- Dates
        case
            when show_date like '%/%'
            then
                try_cast(
                    concat(
                        split_part(show_date, '/', 3),
                        '-',
                        lpad(split_part(show_date, '/', 1), 2, '0'),
                        '-',
                        lpad(split_part(show_date, '/', 2), 2, '0')
                    ) as date
                )
            else try_cast(show_date as date)
        end as show_date,

        -- Location
        city_name,
        state_code,
        country_name,
        market_size,

        -- Venue details
        venue_type,
        venue_capacity,

        -- Artist details
        artist_tier,

        -- Ticket sales
        try_cast(tickets_sold as int) as tickets_sold,
        case
            when lower(sellout_status) = 'true' then true
            when lower(sellout_status) = 'false' then false
        end as is_sellout,
        try_cast(attendance_rate as float) as attendance_rate,

        -- Pricing
        try_cast(average_ticket_price as float) as average_ticket_price,
        ticket_price_range,
        try_cast(revenue as float) as revenue,

        -- Metadata
        source,
        last_updated,
        ingested_at

    from source_data
    where
        show_date is not null
        and artist_name is not null
        and venue_name is not null
)

select
    artist_id,
    artist_name,
    show_id,
    venue_id,
    venue_name,
    show_date,
    city_name,
    state_code,
    country_name,
    market_size,
    venue_type,
    venue_capacity,
    artist_tier,
    tickets_sold,
    is_sellout,
    attendance_rate,
    average_ticket_price,
    ticket_price_range,
    revenue,
    source,
    last_updated,
    ingested_at
from cleaned_data
