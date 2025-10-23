

with source_data as (
  select
    ARTIST_ID,
    ARTIST_NAME,
    SHOW_ID,
    SHOW_DATE,
    SOURCE,
    PAYLOAD,
    INGESTED_AT
  from DB_T4.FAN_RAW.raw_shows
),

flattened as (
  select
    artist_id,
    artist_name,
    show_id,
    show_date,
    source,
    payload:"artist":name::string           as artist_name_api,
    payload:"artist":mbid::string           as artist_mbid_api,
    payload:"venue":name::string            as venue_name,
    payload:"venue":id::string              as venue_id,
    payload:"venue":city:name::string       as city_name,
    payload:"venue":city:stateCode::string  as state_code,
    payload:"venue":city:country:name::string as country_name,
    payload:"eventDate"::string             as event_date_str,
    payload:"lastUpdated"::string           as last_updated,
    ingested_at
  from source_data
),

city_filtered as (
  select *
  from flattened
  where city_name in ( 'Los Angeles','New York','Houston','Chicago','Las Vegas','Nashville','Atlanta' )
),

dedup_same_artist_back_to_back as (
  select *
  from (
    select
      *,
      lag(show_date) over (partition by city_name, artist_name order by show_date) as prev_show_date
    from city_filtered
  )
  where prev_show_date is null
     or datediff('day', prev_show_date, show_date) > 3
),

ranked as (
  select
    *,
    row_number() over (partition by city_name order by show_date desc) as city_show_rank
  from dedup_same_artist_back_to_back
)

select *
from ranked
where city_show_rank <= 3