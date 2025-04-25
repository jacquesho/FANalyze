-- This statement parses raw JSON data from STAGING_SETLISTS into a clean, structured FACT_SETLISTS table.
-- Transformations include:
--   • Type Conversion: song names extracted from JSON and cast to STRING.
--   • Cleaning: TRIM used on song names.
--   • Ordering: set_index and song_index used to build global order across multiple sets.
--   • Row Numbering: assigns final song_position per setlist.

INSERT INTO FANALYZE.PUBLIC.FACT_SETLISTS (
  SHOW_ID,
  SONG_NAME,
  SONG_POSITION
)
WITH sets AS (
  SELECT
    s.show_id,
    f.index AS set_index,
    f.value AS set_block
  FROM FANALYZE.PUBLIC.STAGING_SETLISTS s,
       LATERAL FLATTEN(input => s.setlist:set) f
),
songs AS (
  SELECT
    s.show_id,
    s.set_index,
    f.value:name::STRING AS song_name,
    f.index AS song_index
  FROM sets s,
       LATERAL FLATTEN(input => s.set_block:song) f
),
cleaned AS (
  SELECT
    show_id,
    TRIM(song_name) AS song_name,
    (set_index * 1000) + song_index AS order_key
  FROM songs
  WHERE song_name IS NOT NULL AND TRIM(song_name) <> ''
),
ordered AS (
  SELECT
    show_id,
    song_name,
    ROW_NUMBER() OVER (PARTITION BY show_id ORDER BY order_key) AS song_position
  FROM cleaned
)
SELECT * FROM ordered;
