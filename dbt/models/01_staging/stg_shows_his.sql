{{ config(materialized='view', schema='STAGING') }}

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
        -- Note: CSV columns are NUMBER(19,0), cast via VARCHAR to avoid TRY_CAST precision mismatch
        try_cast(tickets_sold::VARCHAR as INTEGER) as tickets_sold,
        case
            when lower(sellout_status) = 'true' then true
            when lower(sellout_status) = 'false' then false
        end as is_sellout,
        try_cast(attendance_rate::VARCHAR as FLOAT) as attendance_rate,

        -- Pricing
        try_cast(average_ticket_price::VARCHAR as FLOAT) as average_ticket_price,
        ticket_price_range,
        try_cast(revenue::VARCHAR as FLOAT) as revenue,

        -- Metadata
        source,
        last_updated,
        ingested_at,

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
