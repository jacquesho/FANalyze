{{ config(materialized='view') }}

with source_data as (
    select * from {{ source('raw_data', 'shows_future') }}
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
        try_cast(show_date_parsed as date) as show_date_parsed,
        
        -- Location
        city_name,
        state_code,
        country_name,
        
        -- Metadata
        source,
        collected_at
        
    from source_data
    where show_date is not null
      and artist_name is not null
      and venue_name is not null
)

select * from cleaned_data
