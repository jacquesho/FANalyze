# dbt Ticket Data Transformation Workflow

## Overview

This document describes the dbt transformation pipeline for ticket sales data. Once streaming ticket data is loaded into `FAN_RAW.raw_tickets`, dbt transforms it through three layers (Staging → Intermediate → Marts) to create analytics-ready tables.

---

## Data Flow Architecture

```
FAN_RAW (Raw Data)
    ↓
STAGING (Cleaning & Standardization)
    ↓
INTERMEDIATE (Business Logic & Deduplication)
    ↓
MARTS (Analytics-Ready Tables)
```

---

## Layer 1: STAGING (`01_staging/`)

**Purpose:** Clean, validate, and standardize raw data

### Key Models:

#### `stg_ticket_sales`
- **Source:** `FAN_RAW.raw_tickets` (streaming ticket sales events)
- **What it does:**
  - Filters out invalid records (null show_id, artist_name, etc.)
  - Cleans negative values (tickets_sold, revenue, venue_capacity)
  - Generates unique `ticket_sales_key` using custom macro
  - Calculates `venue_utilization_pct` (cumulative tickets / capacity)
  - Calculates `sales_velocity_per_day` using custom macro
- **Output:** Cleaned ticket sales events with calculated metrics

---

## Layer 2: INTERMEDIATE (`02_intermediate/`)

**Purpose:** Apply business logic, deduplicate, and prepare for final models

### Key Models:

#### `int_ticket_sales_dedup`
- **Source:** `stg_ticket_sales`
- **What it does:**
  - **Deduplicates** ticket sales events by `ticket_sales_key`
  - Keeps the **latest record** per key (by timestamp, created_at, id)
  - Ensures each unique sales event appears only once
- **Why:** Streaming data may have duplicate events; this ensures data quality
- **Output:** Deduplicated ticket sales events

---

## Layer 3: MARTS (`03_marts/`)

**Purpose:** Create analytics-ready fact and dimension tables

### Fact Tables:

#### `fact_ticket_sales` ⭐ **Core Table**
- **Source:** `int_ticket_sales_dedup`
- **Materialization:** Incremental (merge strategy)
- **What it does:**
  - Creates incremental fact table (only processes new records since last run)
  - Adds business logic:
    - `demand_category` (High/Medium/Low/Very Low Demand based on sales_rate)
    - `time_to_show_category` (Last Week/Month/Quarter/Future)
    - `revenue_per_ticket`
  - Tracks `dbt_updated_at` and `dbt_created_at` timestamps
- **Use case:** Detailed ticket sales event analysis
- **Key fields:** ticket_sales_key, show_id, timestamp, tickets_sold, revenue, sales_rate, demand_category

### Mart Tables (Analytics Aggregations):

#### `marts_ticket_performance` ⭐ **Key Analytics Table**
- **Source:** `fact_ticket_sales`
- **What it does:**
  - **Aggregates** ticket sales events to **show-level** metrics
  - Calculates per-show metrics:
    - `total_sales_events` - Number of sales events for the show
    - `total_tickets_sold` - Sum of all tickets sold
    - `final_tickets_sold` - Maximum cumulative tickets (final count)
    - `final_revenue` - Maximum cumulative revenue (final total)
    - `final_sales_rate` - Maximum sales rate achieved
    - `overall_sales_velocity` - Average tickets sold per day
    - `performance_rating` - Excellent/Good/Average/Below Average/Poor
    - `capacity_category` - Sold Out/Near Capacity/Half Full/etc.
- **Use case:** Analyze show performance, identify best/worst performing shows
- **Key fields:** show_id, artist_name, venue_name, show_date, final_revenue, performance_rating

#### `marts_daily_ticket_summary`
- **Source:** `fact_ticket_sales`
- **What it does:**
  - **Daily aggregations** by artist, city, state, tier
  - Daily metrics:
    - `daily_tickets_sold`, `daily_revenue`
    - `daily_sales_events` - Number of sales events that day
    - `shows_with_sales` - Number of different shows with sales
    - `avg_daily_sales_rate`, `avg_daily_sales_velocity`
    - `high_demand_events`, `medium_demand_events`, `low_demand_events`
    - `daily_performance_rating` - Excellent/Good/Average/Below Average/Poor Day
- **Use case:** Daily performance tracking, trend analysis
- **Key fields:** sale_date, artist_name, city_name, daily_revenue, daily_performance_rating

---

## Key Concepts

### Incremental Processing
- `fact_ticket_sales` uses **incremental materialization**
- Only processes new records since the last dbt run
- Efficient for streaming data that grows continuously

### Deduplication Strategy
- Streaming data may have duplicate events
- `int_ticket_sales_dedup` ensures each unique sales event appears once
- Uses `ticket_sales_key` (generated from show_id + timestamp) as natural key

### Custom Macros
- `generate_ticket_sales_key()` - Creates unique identifier for sales events
- `calculate_sales_velocity()` - Calculates tickets sold per day metric

### Data Quality Checks
- Staging layer filters out invalid records (nulls, negative values)
- Tests defined in `schema.yml` files ensure data quality
- Business logic validates data before it reaches marts

---

## Typical Query Patterns

### Show Performance Analysis
```sql
SELECT 
    show_id,
    artist_name,
    venue_name,
    show_date,
    final_revenue,
    final_tickets_sold,
    performance_rating
FROM MARTS.marts_ticket_performance
WHERE performance_rating IN ('Excellent', 'Good')
ORDER BY final_revenue DESC
```

### Daily Sales Trends
```sql
SELECT 
    sale_date,
    artist_name,
    daily_revenue,
    daily_tickets_sold,
    daily_performance_rating
FROM MARTS.marts_daily_ticket_summary
WHERE sale_date >= CURRENT_DATE - 30
ORDER BY sale_date DESC, daily_revenue DESC
```

### Detailed Event Analysis
```sql
SELECT 
    timestamp,
    show_id,
    artist_name,
    tickets_sold,
    revenue,
    demand_category,
    sales_velocity_per_day
FROM MARTS.fact_ticket_sales
WHERE show_id = 'SHOW123'
ORDER BY timestamp DESC
```

---

## Execution Order

When `dbt run` executes, models run in dependency order:

1. **Staging models** run first (depend only on sources)
2. **Intermediate models** run next (depend on staging)
3. **Marts models** run last (depend on intermediate and staging)

Within each layer, models can run in parallel if they don't depend on each other.

---

## Summary

**From Raw to Analytics:**
1. **FAN_RAW.raw_tickets** → Raw streaming events
2. **STAGING.stg_ticket_sales** → Cleaned and standardized
3. **INTERMEDIATE.int_ticket_sales_dedup** → Deduplicated
4. **MARTS.fact_ticket_sales** → Incremental fact table (detailed events)
5. **MARTS.marts_ticket_performance** → Show-level aggregations
6. **MARTS.marts_daily_ticket_summary** → Daily aggregations

The pipeline ensures data quality, handles duplicates, and creates multiple views of the data optimized for different analytical use cases.
