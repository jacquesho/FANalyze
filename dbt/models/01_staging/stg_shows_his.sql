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
