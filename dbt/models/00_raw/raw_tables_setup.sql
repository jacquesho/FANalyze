{{ config(materialized='table') }}

-- This model runs the table creation macro
-- It's a placeholder that ensures the macro runs during dbt execution

{{ create_raw_tables() }}

select 1 as setup_complete
