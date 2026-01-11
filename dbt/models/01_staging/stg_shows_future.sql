{{ config(materialized='view', schema='staging') }}

with source_data as (
    select * from {{ source('FAN_RAW', 'shows_future') }}
),

cleaned_data as (
    select
        -- Identifiers
        show_id,
        venue_id,
        -- Basic info
        artist_name,
        venue_name,
        -- Dates
        try_cast(show_date as date) as show_date,
        try_cast(collected_at as timestamp) as collected_at,
        -- Location
        city_name,
        state_code,
        country_name,
        -- Metadata
        source
    from source_data
    where
        show_date is not null
        and artist_name is not null
        and venue_name is not null
)

select
    show_id,
    venue_id,
    artist_name,
    venue_name,
    show_date,
    collected_at,
    city_name,
    state_code,
    country_name,
    source
from cleaned_data
