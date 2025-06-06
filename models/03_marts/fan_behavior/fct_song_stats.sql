{{ config(materialized='table') }}

select
    artist_name,
    song_name,
    count(*) as play_count,
    min(event_date) as first_play,
    max(event_date) as last_play
from {{ ref('int_setlists_flat') }}
where song_name is not null

  -- ❌ Exclude Metallica intro/interlude tracks for M72
  and not (
    artist_name = 'Metallica'
    and song_name in (
      'The Ecstasy of Gold',
      'It\'s a Long Way to the Top (If You Wanna Rock \'n\' Roll)',
      'Kirk and Rob Doodle'
    )
  )

group by artist_name, song_name
order by play_count desc
