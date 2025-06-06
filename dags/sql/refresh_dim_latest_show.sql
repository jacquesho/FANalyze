-- refresh_dim_latest_show.sql
create or replace table DB_FANALYZE.FANALYZE.DIM_LATEST_SHOW_PER_ARTIST as
select
  artist_id,
  max(event_date) as latest_known_show
from DB_FANALYZE.FANALYZE.STG_SHOWS
group by artist_id;
