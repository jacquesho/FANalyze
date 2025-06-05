{{ config(materialized='view') }}

select * from {{ ref('stg_setlists_raw') }}
union all
select * from {{ ref('stg_setlists_inc') }}
