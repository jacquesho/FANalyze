{{ config(materialized='view', schema='STAGING') }}

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
        collected_at,

        -- Location
        city_name,
        state_code,
        country_name,

        -- Metadata
        source,

        -- Data Quality Flags
        case 
            when show_date is null then true 
            else false 
        end as has_missing_date,
        case 
            when artist_name is null then true 
            else false 
        end as has_missing_artist,
        case 
            when venue_name is null then true 
            else false 
        end as has_missing_venue,
        case 
            when show_id is null then true 
            else false 
        end as has_missing_show_id,
        
        -- Overall data quality status
        case
            when show_date is null and artist_name is null and venue_name is null then 'Incomplete'
            when show_date is null or artist_name is null or venue_name is null then 'Partial'
            else 'Complete'
        end as data_quality_status,
        
        -- Completeness score (0-100%)
        round(
            (case when show_date is not null then 1 else 0 end +
             case when artist_name is not null then 1 else 0 end +
             case when venue_name is not null then 1 else 0 end +
             case when show_id is not null then 1 else 0 end) * 25.0,
            2
        ) as completeness_score

    from source_data
    -- Keep all records - filter by data quality flags downstream if needed
)

select * from cleaned_data
