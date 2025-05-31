-- fct_song_stats.sql
-- ------------------------------------------------------------------------------
-- Description : Fact table calculating the number of times each song has
--               been played by an artist across all shows.
-- Source      : Flattened JSON from staging_setlists, joined with show metadata.
-- Purpose     : Enables insights into fan-favorite songs and artist setlist trends.
-- ------------------------------------------------------------------------------

WITH flattened AS (
  SELECT
    ss.artist_id,
    f.value:name::STRING AS song_name_raw
  FROM {{ source('setlistfm', 'staging_setlists') }} s
  JOIN {{ source('setlistfm', 'staging_shows') }} ss
    ON s.show_id = ss.show_id,
       LATERAL FLATTEN(input => s.setlist:set[0].song) f
),
cleaned AS (
  SELECT
    TRIM(artist_id) AS artist_id,
    TRIM(song_name_raw) AS song_name
  FROM flattened
  WHERE song_name_raw IS NOT NULL AND TRIM(song_name_raw) <> ''
),
aggregated AS (
  SELECT
    artist_id,
    song_name,
    COUNT(*) AS play_count
  FROM cleaned
  GROUP BY artist_id, song_name
)
SELECT * FROM aggregated
