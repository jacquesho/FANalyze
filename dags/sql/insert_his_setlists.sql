-- file: insert_staging_setlists.sql  (comes in via JSON) 
INSERT INTO DB_FANALYZE.FANALYZE.STG_SETLISTS_RAW (
  SHOW_ID,
  SETLIST,
  LOAD_TYPE
)
WITH parsed_setlists AS (
  SELECT
    METADATA$FILENAME                                AS source_file,
    METADATA$FILE_ROW_NUMBER                         AS row_number,
    src.value:id::STRING                             AS show_id,
    src.value                                        AS setlist
  FROM @DB_FANALYZE.FANALYZE.RAW_SETLISTS_STAGE (
    FILE_FORMAT => 'DB_FANALYZE.FANALYZE.JSON_FORMAT'
  ) t,
  LATERAL FLATTEN(input => t.$1) src
)
SELECT
  show_id,
  setlist,
  'Historical' AS load_type
FROM parsed_setlists;
