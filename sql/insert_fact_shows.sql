
-- This statement inserts cleaned show-level concert data into the FACT_SHOWS table.
-- Transformations include:
--   • Cleaning: TRIM is used on string fields for consistency.
--   • Deduplication: SELECT DISTINCT ensures no duplicate shows are inserted.

INSERT INTO FANALYZE.PUBLIC.FACT_SHOWS (
  SHOW_ID,
  ARTIST_ID,
  SHOW_DATE,
  VENUE,
  CITY,
  COUNTRY,
  TOUR_NAME,
  TICKET_TIER,
  SIMULATED_PRICE_USD
)
SELECT DISTINCT
  SHOW_ID,
  ARTIST_ID,
  SHOW_DATE,
  TRIM(VENUE),
  TRIM(CITY),
  TRIM(COUNTRY),
  TRIM(TOUR_NAME),
  TICKET_TIER,
  SIMULATED_PRICE_USD
FROM FANALYZE.PUBLIC.STAGING_SHOWS
WHERE ARTIST_ID IS NOT NULL AND SHOW_ID IS NOT NULL;
