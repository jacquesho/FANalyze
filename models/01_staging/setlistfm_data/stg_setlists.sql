{{ config(materialized='view') }}

with raw as (
    select
        show_id,
        setlist
    from {{ source('setlistfm_data', 'stg_setlists_raw') }}
),

flattened_sets as (
    select
        raw.show_id,
        song.value:name::string as song_name,
        row_number() over (
            partition by raw.show_id, s.index
            order by song.index
        ) as song_order
    from raw,
         lateral flatten(input => parse_json(setlist):sets.set) as s,
         lateral flatten(input => s.value:song) as song
)

select * from flattened_sets
