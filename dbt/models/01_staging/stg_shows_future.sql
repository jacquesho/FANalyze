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
        (show_date IS NULL) AS has_missing_date,
        (artist_name IS NULL) AS has_missing_artist,
        (venue_name IS NULL) AS has_missing_venue,
        (show_id IS NULL) AS has_missing_show_id,

        -- Overall data quality status
        CASE
            WHEN show_date IS NULL AND artist_name IS NULL AND venue_name IS NULL THEN 'Incomplete'
            WHEN show_date IS NULL OR artist_name IS NULL OR venue_name IS NULL THEN 'Partial'
            ELSE 'Complete'
        END AS data_quality_status,

        -- Completeness score (0-100%)
        ROUND(
            (
                CASE WHEN show_date IS NOT NULL THEN 1 ELSE 0 END
                + CASE WHEN artist_name IS NOT NULL THEN 1 ELSE 0 END
                + CASE WHEN venue_name IS NOT NULL THEN 1 ELSE 0 END
                + CASE WHEN show_id IS NOT NULL THEN 1 ELSE 0 END
            ) * 25.0,
            2
        ) AS completeness_score

    from source_data
    -- Keep all records - filter by data quality flags downstream if needed
)

select * from cleaned_data
