-- Checks for duplicate show_id

SELECT show_id, COUNT(*) as count
FROM {{ ref('stg_shows') }}
GROUP BY show_id
HAVING COUNT(*) > 1
