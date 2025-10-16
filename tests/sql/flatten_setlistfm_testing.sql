-- Flatten JSON payloads from testing.raw_shows and testing.raw_setlists
-- Mirrors the idea of 01_staging in v1.0 by extracting typed columns

CREATE SCHEMA IF NOT EXISTS testing;

CREATE OR REPLACE TABLE testing.flat_shows AS
SELECT
  rs.artist_id,
  rs.artist_name,
  rs.show_id,
  TO_DATE(rs.show_date, 'DD-MM-YYYY') AS show_date,
  rs.source,
  -- Common flattened fields
  rs.payload:artist:name::string            AS artist_name_api,
  rs.payload:artist:mbid::string            AS artist_mbid_api,
  rs.payload:venue:name::string             AS venue_name,
  rs.payload:venue:id::string               AS venue_id,
  rs.payload:venue:city:name::string        AS city_name,
  rs.payload:venue:city:stateCode::string   AS state_code,
  rs.payload:venue:city:country:name::string AS country_name,
  rs.payload:eventDate::string              AS event_date_str,
  rs.payload:lastUpdated::string            AS last_updated,
  rs.ingested_at
FROM testing.raw_shows rs;

-- Optional helpful indexes
CREATE INDEX IF NOT EXISTS idx_flat_shows_artist_date ON testing.flat_shows(artist_id, show_date);



