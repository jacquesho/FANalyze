{{ config(materialized='view') }}

select * from {{ source('setlistfm_data', 'stg_setlists_raw') }}
union all
select * from {{ source('setlistfm_data', 'stg_setlists_sch') }}

