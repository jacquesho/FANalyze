{{ config(materialized='table', enabled=false) }}

-- This model is disabled since tables already exist
-- Tables were created manually via the Python ingestion script

select 1 as setup_complete
