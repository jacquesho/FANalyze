-- dim_artists.sql
-- ------------------------------------------------------------------------------
-- Description : Dimension table containing curated metadata about artists.
--               Includes unique IDs, names, and associated genres.
-- Source      : Static in-model values (manually defined).
-- Purpose     : Used for joining with fact tables to enrich analytics with
--               artist details such as name and genre.
-- ------------------------------------------------------------------------------


SELECT
  '65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab' AS artist_id,
  'Metallica' AS artist_name,
  'Heavy Metal, Thrash Metal, Speed Metal, Hard Rock' AS artist_genre
UNION ALL
SELECT 'e73db0bc-22eb-4589-9c6b-f35ad14f5647', 'Nita Strauss', 'Hard Rock, Heavy Metal, Power Metal, Speed/Thrash Metal'
UNION ALL
SELECT '5e7ccd92-6277-451a-aab9-1efd587c50f3', 'Steve Vai', 'instrumental rock, rock, avant-garde metal, experimental, hard rock'


/* Additional artist data, pending for project growth.  Using smaller bands for now.

UNION ALL
SELECT '4e478f4f-a1e5-4ac9-84a3-f58f5c6454ab', 'Bloodywood', 'Nu Metal, Folk Metal, Rap Metal, Metalcore'
UNION ALL
SELECT 'e631bb92-3e2b-43e3-a2cb-b605e2fb53bd', 'Arch Enemy', 'Melodic Death Metal'
UNION ALL
SELECT '7f625f35-7e53-4f08-9201-16643979484b', 'The Warning', 'Hard Rock, Alternative Rock, Post-Grunge'
UNION ALL
SELECT '49a6efb9-9b52-44ce-8167-7cb1c21a8c45', 'Mammoth WVH', 'Hard Rock, Alternative Rock'
UNION ALL
SELECT 'eaed2193-e026-493b-ac57-113360407b06', 'Halestorm', 'Hard Rock, Heavy Metal, Alternative Metal, Post-Grunge'
UNION ALL
SELECT 'ca891d65-d9b0-4258-89f7-e6ba29d83767', 'Iron Maiden', 'Heavy Metal, New Wave of British Heavy Metal';
UNION ALL
SELECT 'f59c5520-5f46-4d2c-b2c4-822eabf53419', 'Linkin Park', 'Alternative Rock, Nu Metal, Rap Rock'
UNION ALL
SELECT '4bb4e4e4-5f66-4509-98af-62dbb90c45c5', 'Disturbed', 'Heavy Metal, Alternative Metal, Nu Metal'

*/