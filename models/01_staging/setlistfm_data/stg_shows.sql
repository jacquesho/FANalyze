{{ config(materialized='view') }}

-- stg_shows.sql
-- ------------------------------------------------------------------------------
-- Description : Staging model that cleans raw concert show data.
--               Trims string fields and filters out invalid or incomplete rows.
-- Source      : stg_shows_raw table from the source database.
-- Purpose     : Provides a clean base for downstream transformations like
--               flattened setlists and song statistics.
-- ------------------------------------------------------------------------------

with source as (
    select *
    from {{ ref('stg_shows_combined') }}
)

select
    show_id,
    artist_id,
    artist_name,
    tour_name,
    show_date::date as event_date,
    trim(venue) as venue,
    trim(city) as city,
    trim(country) as country,
    ticket_tier,
    simulated_price_usd,
    load_type,
    current_timestamp() as ingestion_ts

from source

select * from source
