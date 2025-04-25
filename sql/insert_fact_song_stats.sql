
-- This query aggregates how often each song is performed per artist into the FACT_SONG_STATS table.
-- Transformations include:
--   • Type Conversion: song names extracted from JSON and cast to STRING.
--   • Cleaning: TRIM removes whitespace from artist_id and song_name.
--   • Aggregation: COUNT(*) to compute total number of times each song appears per artist.

INSERT INTO FANALYZE.PUBLIC.FACT_SONG_STATS (
  ARTIST_ID,
  SONG_NAME,
  PLAY_COUNT
)
WITH flattened AS (
  SELECT
    ss.artist_id,
    f.value:name::STRING AS song_name_raw
  FROM FANALYZE.PUBLIC.STAGING_SETLISTS s
  JOIN FANALYZE.PUBLIC.STAGING_SHOWS ss
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
SELECT * FROM aggregated;
