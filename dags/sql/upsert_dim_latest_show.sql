-- file: upsert_dim_latest_show.sql

merge into DB_FANALYZE.FANALYZE.DIM_LATEST_SHOW_PER_ARTIST as target
using (
  select
    artist_id,
    max(show_date) as latest_known_show
  from DB_FANALYZE.FANALYZE.STG_SHOWS_RAW
  group by artist_id
) as source
on target.artist_id = source.artist_id

when matched and source.latest_known_show > target.latest_known_show then
  update set target.latest_known_show = source.latest_known_show

when not matched then
  insert (artist_id, latest_known_show)
  values (source.artist_id, source.latest_known_show);
