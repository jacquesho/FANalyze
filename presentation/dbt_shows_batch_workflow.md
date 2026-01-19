# dbt Shows Batch Data Transformation Workflow

## Overview

This document describes the dbt transformation pipeline for shows data from batch CSV ingestion. Once show data is loaded into `FAN_RAW.shows_his` and `FAN_RAW.shows_future`, dbt transforms it through three layers (Staging → Intermediate → Marts) to create analytics-ready tables for show, artist, and venue analysis.

**Note:** This workflow is independent of the streaming ticket sales workflow. These models process batch CSV data about shows, artists, and venues.

---

## Data Flow Architecture

```
FAN_RAW (Raw CSV Data)
    ├── shows_his (Historical shows)
    └── shows_future (Upcoming shows)
         ↓
STAGING (Cleaning & Standardization)
    ├── stg_shows_his
    └── stg_shows_future
         ↓
INTERMEDIATE (Business Logic & Aggregations)
    ├── int_shows
    ├── int_artists
    ├── int_venues
    └── int_show_lifecycle
         ↓
MARTS (Analytics-Ready Tables)
    ├── fact_shows (Unified fact table)
    ├── dim_artists
    ├── dim_venues
    ├── marts_artist_performance
    └── marts_show_lifecycle
```

---

## Layer 1: STAGING (`01_staging/`)

**Purpose:** Clean, validate, and standardize raw CSV show data

### Key Models:

#### `stg_shows_his`
- **Source:** `FAN_RAW.shows_his` (historical shows CSV)
- **What it does:**
  - Cleans date formats (handles MM/DD/YYYY format)
  - Validates required fields (show_date, artist_name, venue_name)
  - Type conversions (tickets_sold, revenue, attendance_rate, etc.)
  - Boolean conversion for `is_sellout` field
  - Filters out records with null show_date, artist_name, or venue_name
- **Output:** Cleaned historical show records with standardized data types

#### `stg_shows_future`
- **Source:** `FAN_RAW.shows_future` (upcoming shows CSV)
- **What it does:**
  - Standardizes show data structure
  - Validates required fields (show_id, show_date, venue_name, artist_name)
  - Ensures unique show_id values
- **Output:** Cleaned upcoming show records

---

## Layer 2: INTERMEDIATE (`02_intermediate/`)

**Purpose:** Apply business logic, create aggregations, and prepare dimensional data

### Key Models:

#### `int_shows`
- **Source:** `stg_shows_his`
- **What it does:**
  - Enriches show data with calculated metrics:
    - `calculated_attendance_rate` (tickets_sold / venue_capacity)
    - `calculated_sellout` (boolean based on tickets_sold >= capacity)
    - `revenue_per_ticket` (revenue / tickets_sold)
    - Date parts: `show_year`, `show_month`, `show_quarter`, `day_of_week`
    - `season` (Winter, Spring, Summer, Fall)
- **Output:** Enriched show data ready for fact table

#### `int_artists`
- **Source:** `stg_shows_his` + `stg_shows_future`
- **What it does:**
  - **Aggregates** artist performance metrics from historical shows:
    - `total_shows` - Count of shows performed
    - `first_show_date`, `last_show_date` - Date range
    - `avg_attendance_rate`, `avg_ticket_price`
    - `total_revenue`, `total_tickets_sold`
  - **Enriches** with upcoming shows count from `stg_shows_future`
  - Adds `has_upcoming_shows` flag
- **Output:** Artist-level aggregated metrics

#### `int_venues`
- **Source:** `stg_shows_his` + `stg_shows_future`
- **What it does:**
  - **Aggregates** venue performance metrics:
    - `total_shows` - Count of shows hosted
    - `unique_artists` - Number of different artists
    - `avg_attendance_rate`, `avg_ticket_price`
    - `total_revenue`, `total_tickets_sold`
    - `sellout_count` - Number of sellout shows
    - `sellout_rate` - Percentage of shows that sold out
    - `first_show_date`, `last_show_date`
  - **Enriches** with upcoming shows count
- **Output:** Venue-level aggregated metrics

#### `int_show_lifecycle`
- **Source:** `stg_shows_future` + `stg_shows_his`
- **What it does:**
  - **Tracks** shows that have moved from upcoming to historical status
  - Identifies shows that need status updates
  - Tracks data completeness for upcoming shows
- **Output:** Show lifecycle change tracking

---

## Layer 3: MARTS (`03_marts/`)

**Purpose:** Create analytics-ready fact and dimension tables

### Fact Tables:

#### `fact_shows` ⭐ **Core Table**
- **Source:** `int_shows` + `stg_shows_future`
- **What it does:**
  - **Unifies** historical and upcoming shows into single fact table
  - Adds business metrics:
    - `sales_performance` (Near Sellout/Good/Average/Low Sales) - for historical shows
    - `revenue_tier` (High/Medium/Low/Very Low Revenue) - for historical shows
    - `time_status` (Past/Today/This Week/This Month/Future)
    - `weekend_show` flag (weekend vs weekday)
    - `days_from_show` (negative for past, positive for future)
  - Tracks `show_status` (Historical vs Upcoming)
  - Includes `ingested_at` timestamp
- **Use case:** Show-level analysis across all shows (past and future)
- **Key fields:** show_id, artist_id, venue_id, show_date, show_status, tickets_sold, revenue, sales_performance

### Dimension Tables:

#### `dim_artists`
- **Source:** `int_artists`
- **What it does:**
  - Creates artist master dimension table
  - Adds calculated metrics:
    - `avg_revenue_per_show` - Average revenue per show
    - `avg_tickets_per_show` - Average tickets sold per show
    - `tier_classification` - Standardized tier (Tier 1/2/3)
    - `activity_status` - Active/Recently Active/Inactive based on last show date
- **Use case:** Artist master data for dimensional analysis
- **Key fields:** artist_id, artist_name, artist_tier, total_shows, total_revenue, activity_status

#### `dim_venues`
- **Source:** `int_venues`
- **What it does:**
  - Creates venue master dimension table
  - Adds calculated metrics:
    - `avg_revenue_per_show` - Average revenue per show
    - `avg_tickets_per_show` - Average tickets per show
    - `venue_size_class` - Stadium/Arena/Large Theater/Theater/Small Venue
    - `performance_tier` - High/Good/Average/Low Performance based on attendance
- **Use case:** Venue master data for dimensional analysis
- **Key fields:** venue_id, venue_name, venue_type, venue_capacity, city_name, total_shows, sellout_rate

### Mart Tables (Analytics Aggregations):

#### `marts_artist_performance` ⭐ **Key Analytics Table**
- **Source:** `dim_artists` + `fact_shows`
- **What it does:**
  - **Artist-level** performance analytics and rankings
  - Calculates:
    - `revenue_rank`, `tickets_rank`, `attendance_rank` - Performance rankings
    - `revenue_market_share`, `tickets_market_share` - Market share percentages
    - `unique_venues`, `unique_cities`, `unique_states` - Geographic diversity
    - `performance_category` - Top/High/Medium/Low Performer
    - `growth_potential` - High/Moderate/No Growth based on upcoming shows
- **Use case:** Artist performance analysis, identify top performers, market share analysis
- **Key fields:** artist_id, artist_name, total_revenue, revenue_rank, revenue_market_share, performance_category

#### `marts_show_lifecycle`
- **Source:** `fact_shows` + `dim_artists`
- **What it does:**
  - **Tracks** shows through lifecycle stages
  - Identifies:
    - `status_consistency` - Whether show status matches its date
    - `data_completeness` - Complete/Partial/Basic for upcoming shows
    - `update_priority` - High/Medium/Low/None based on data needs
    - `recommended_action` - Update Status/Urgent Data Update/etc.
  - Matches upcoming shows with historical artist data
- **Use case:** Data quality monitoring, identifying shows needing updates
- **Key fields:** show_id, show_status, time_status, data_completeness, update_priority, recommended_action

---

## Key Concepts

### Unified Fact Table
- `fact_shows` combines historical and upcoming shows
- Historical shows have complete data (tickets_sold, revenue, etc.)
- Upcoming shows may have partial or no sales data (will be updated as data becomes available)

### Dimensional Modeling
- `dim_artists` and `dim_venues` provide master data
- Fact table references dimensions via foreign keys (artist_id, venue_id)
- Enables dimensional analysis (drill-down by artist, venue, etc.)

### Show Lifecycle Tracking
- Tracks shows as they move from "Upcoming" to "Historical"
- Identifies data quality issues and update priorities
- Helps maintain data consistency across time

### Aggregation Strategy
- Artist and venue metrics aggregated from show-level data
- Performance rankings calculated across all artists/venues
- Market share calculated as percentage of total market

---

## Typical Query Patterns

### Top Performing Artists
```sql
SELECT 
    artist_name,
    artist_tier,
    total_revenue,
    revenue_rank,
    revenue_market_share,
    performance_category
FROM MARTS.marts_artist_performance
WHERE performance_category IN ('Top Performer', 'High Performer')
ORDER BY revenue_rank
```

### Venue Performance Analysis
```sql
SELECT 
    venue_name,
    city_name,
    venue_size_class,
    total_shows,
    sellout_rate,
    avg_attendance_rate,
    performance_tier
FROM MARTS.dim_venues
WHERE performance_tier IN ('High Performance', 'Good Performance')
ORDER BY total_revenue DESC
```

### Show Status Monitoring
```sql
SELECT 
    show_id,
    artist_name,
    show_date,
    show_status,
    time_status,
    data_completeness,
    update_priority,
    recommended_action
FROM MARTS.marts_show_lifecycle
WHERE update_priority IN ('High', 'Medium')
ORDER BY show_date
```

### Historical vs Upcoming Shows
```sql
SELECT 
    show_status,
    COUNT(*) AS show_count,
    SUM(CASE WHEN tickets_sold IS NOT NULL THEN tickets_sold ELSE 0 END) AS total_tickets,
    SUM(CASE WHEN revenue IS NOT NULL THEN revenue ELSE 0 END) AS total_revenue
FROM MARTS.fact_shows
GROUP BY show_status
```

---

## Execution Order

When `dbt run` executes, models run in dependency order:

1. **Staging models** run first:
   - `stg_shows_his` and `stg_shows_future` (can run in parallel)

2. **Intermediate models** run next:
   - `int_shows` (depends on `stg_shows_his`)
   - `int_artists` (depends on `stg_shows_his` + `stg_shows_future`)
   - `int_venues` (depends on `stg_shows_his` + `stg_shows_future`)
   - `int_show_lifecycle` (depends on `stg_shows_his` + `stg_shows_future`)

3. **Marts models** run last:
   - `fact_shows` (depends on `int_shows` + `stg_shows_future`)
   - `dim_artists` (depends on `int_artists`)
   - `dim_venues` (depends on `int_venues`)
   - `marts_artist_performance` (depends on `dim_artists` + `fact_shows`)
   - `marts_show_lifecycle` (depends on `fact_shows` + `dim_artists`)

---

## Summary

**From Raw CSV to Analytics:**
1. **FAN_RAW.shows_his** → Historical shows CSV
2. **FAN_RAW.shows_future** → Upcoming shows CSV
3. **STAGING.stg_shows_his** → Cleaned historical shows
4. **STAGING.stg_shows_future** → Cleaned upcoming shows
5. **INTERMEDIATE.int_shows** → Enriched show data
6. **INTERMEDIATE.int_artists** → Artist aggregations
7. **INTERMEDIATE.int_venues** → Venue aggregations
8. **MARTS.fact_shows** → Unified fact table (historical + upcoming)
9. **MARTS.dim_artists** → Artist dimension
10. **MARTS.dim_venues** → Venue dimension
11. **MARTS.marts_artist_performance** → Artist-level analytics
12. **MARTS.marts_show_lifecycle** → Show lifecycle tracking

The pipeline creates a comprehensive view of shows, artists, and venues from batch CSV data, enabling dimensional analysis, performance rankings, and lifecycle management.
