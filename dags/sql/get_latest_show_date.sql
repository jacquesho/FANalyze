/* SELECT
  MAX(latest_known_show) AS latest_known_show
FROM DB_FANALYZE.FANALYZE.DIM_LATEST_SHOW_PER_ARTIST
WHERE artist_id = '{{ params.artist_id }}';
*/

SELECT COALESCE(MAX(latest_known_show), '1900-01-01') AS latest_date
FROM DB_FANALYZE.FANALYZE.DIM_LATEST_SHOW_PER_ARTIST
WHERE artist_id = '65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab';
