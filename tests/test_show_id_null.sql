-- Checks for any rows where show_id is null

SELECT *
FROM {{ ref('stg_shows') }}
WHERE show_id IS NULL