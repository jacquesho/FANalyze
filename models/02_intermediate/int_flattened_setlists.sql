-- int_flattened_setlists.sql
-- ------------------------------------------------------------------------------
-- Description : Intermediate model that flattens nested setlist JSON data.
--               Extracts song names, orders them across multiple sets,
--               and assigns song positions per show.
-- Source      : staging_setlists (JSON column with nested song structures).
-- Purpose     : Prepares structured song-level setlist data for fact modeling.
-- ------------------------------------------------------------------------------

WITH sets AS (
  SELECT
    s.show_id,
    f.index AS set_index,
    f.value AS set_block
  FROM {{ source('setlistfm', 'staging_setlists') }} s,
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
SELECT * FROM ordered
