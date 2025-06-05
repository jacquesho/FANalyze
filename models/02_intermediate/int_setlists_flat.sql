{{ config(materialized='table') }}

with shows as (
    select *
    from {{ ref('stg_shows_combined') }}
),

songs as (
    select *
    from {{ ref('stg_setlists') }}
)

select
    s.show_id,
    s.event_date,
    s.artist_name,
    s.tour_name,
    s.city,
    s.country,
    s.venue,
    l.song_order,
    l.song_name,
    current_timestamp() as ingestion_ts
from songs l
join shows s
    on l.show_id = s.show_id
