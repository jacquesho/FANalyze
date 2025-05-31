-- stg_shows.sql
-- ------------------------------------------------------------------------------
-- Description : Staging model that cleans raw concert show data.
--               Trims string fields and filters out invalid or incomplete rows.
-- Source      : staging_shows table from the source database.
-- Purpose     : Provides a clean base for downstream transformations like
--               flattened setlists and song statistics.
-- ------------------------------------------------------------------------------

SELECT DISTINCT
  show_id,
  artist_id,
  show_date,
  TRIM(venue) AS venue,
  TRIM(city) AS city,
  TRIM(country) AS country,
  TRIM(tour_name) AS tour_name,
  ticket_tier,
  simulated_price_usd
FROM {{ source('setlistfm', 'staging_shows') }}
WHERE artist_id IS NOT NULL AND show_id IS NOT NULL
