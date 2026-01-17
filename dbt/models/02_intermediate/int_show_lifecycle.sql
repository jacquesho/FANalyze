{{ config(materialized='table', schema='INTERMEDIATE') }}

with show_status_updates as (
    -- Shows that have moved from upcoming to historical
    select
        fc.show_id,
        'Status Changed' as update_type,
        'Upcoming -> Historical' as change_description,
        current_timestamp as updated_at
    from {{ ref('stg_shows_future') }} as fc
    where
        fc.show_date < current_date
        and not exists (
            select 1
            from {{ ref('stg_shows_his') }} as hs
            where hs.show_id = fc.show_id
        )
),

data_completeness as (
    -- Track which upcoming shows have partial data
    select
        sf.show_id,
        'Basic Info Only' as data_completeness,
        current_timestamp as last_checked
    from {{ ref('stg_shows_future') }} as sf
    where sf.show_date >= current_date
)

select
    show_id,
    update_type,
    change_description,
    updated_at
from show_status_updates

union all

select
    show_id,
    'Data Update' as update_type,
    data_completeness as change_description,
    last_checked as updated_at
from data_completeness
