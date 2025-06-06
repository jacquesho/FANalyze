{{ config(materialized='view') }}

select * from {{ source('setlistfm_data', 'stg_shows_raw') }}
union all
select * from {{ source('setlistfm_data', 'stg_shows_sch') }}

