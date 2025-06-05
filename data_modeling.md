# Data Modeling Approach

## Chosen Approach: Dimensional Modeling

The FANalyze project uses a **dimensional modeling** approach, structured around fact and dimension tables.
This design supports fast, flexible querying and is ideal for analytics and AI-driven exploration.

## Modeling Layers

### Raw Layer
-  Historical (batch) data load
- `stg_shows_raw`: Initial CSV-loaded concert data via Airflow.
- `stg_setlists_raw`: Initial JSON-loaded setlist data via Airflow.

-  Incremental (streaming) data load
- `stg_shows_sch`: Initial CSV-loaded concert data via Airflow.
- `stg_setlists_sch`: Initial JSON-loaded setlist data via Airflow.

### Cleaned Staging
- `stg_shows_combined`, `stg_setlists_combined`: UNION of raw + incremental data.
- `stg_shows`: Cleans fields, casts dates, trims whitespace.
- `stg_setlists`: Flattens nested JSON into song-level rows.

### Intermediate
- `int_setlists_flat`: Joins shows with their setlists; outputs one row per song per show.

### Final Marts
- `fct_song_stats`: Aggregated play counts, first/last appearances, and filtering logic.

### Operational Tables
- `kafka_shows_load`: Logs all Kafka-based show events with timestamp and raw payload.
- `dim_latest_show_per_artist`: Tracks the latest known show per artist, used for incremental API loads.

## Why Dimensional Modeling?
- Easy to query for analytics or AI agents  
- Supports incremental builds and clear lineage  
- Clean separation of raw, logic, and end-user layers  
- Flexible and scalable for new data sources or dimensions

## ERD
See `erd.drawio` or the image version in `docs/images/erd.png`.
