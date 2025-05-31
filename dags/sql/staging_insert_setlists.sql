-- file: insert_staging_setlists.sql
INSERT INTO DB_FANALYZE.STAGING.STAGING_SETLISTS (
  SHOW_ID,
  SETLIST
)
WITH parsed_setlists AS (
  SELECT
    METADATA$FILENAME                                AS source_file,
    METADATA$FILE_ROW_NUMBER                         AS row_number,
    src.value:id::STRING                             AS show_id,
    src.value                                        AS setlist
  FROM @DB_FANALYZE.STAGING.STAGING_SETLISTS_STAGE (
    FILE_FORMAT => 'DB_FANALYZE.STAGING.JSON_FORMAT'
  ) t,
  LATERAL FLATTEN(input => t.$1) src
)
SELECT
  show_id,
  setlist
FROM parsed_setlists;
