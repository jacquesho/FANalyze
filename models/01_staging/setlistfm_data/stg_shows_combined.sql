{{ config(materialized='view') }}

select * from {{ ref('stg_shows_raw') }}
union all
select * from {{ ref('stg_shows_inc') }}
