
  
    

create or replace transient table DB_T4.FAN_staging.stg_ticket_sales
    
    
    
    as (-- Staging layer: Clean and standardize ticket sales data
-- File: models/02_staging/stg_ticket_sales.sql



WITH cleaned_ticket_sales AS (
    SELECT 
        id,
        timestamp,
        show_id,
        artist_name,
        venue_name,
        show_date,
        city_name,
        state_code,
        tickets_sold,
        cumulative_tickets_sold,
        revenue,
        cumulative_revenue,
        venue_capacity,
        sales_rate,
        days_until_show,
        artist_tier,
        average_ticket_price,
        created_at,
        synced_at,
        
        -- Data quality checks
        CASE 
            WHEN tickets_sold < 0 THEN NULL
            ELSE tickets_sold 
        END AS tickets_sold_clean,
        
        CASE 
            WHEN revenue < 0 THEN NULL
            ELSE revenue 
        END AS revenue_clean,
        
        CASE 
            WHEN venue_capacity <= 0 THEN NULL
            ELSE venue_capacity 
        END AS venue_capacity_clean,
        
        -- Generate unique key using custom macro
        
    MD5(CONCAT(show_id, '|', timestamp))
 AS ticket_sales_key
        
    FROM DB_T4.fan_raw.raw_tickets
    WHERE 
        -- Filter out invalid records
        show_id IS NOT NULL
        AND artist_name IS NOT NULL
        AND venue_name IS NOT NULL
        AND show_date IS NOT NULL
        AND timestamp IS NOT NULL
)

SELECT 
    id,
    timestamp,
    show_id,
    artist_name,
    venue_name,
    show_date,
    city_name,
    state_code,
    tickets_sold_clean AS tickets_sold,
    cumulative_tickets_sold,
    revenue_clean AS revenue,
    cumulative_revenue,
    venue_capacity_clean AS venue_capacity,
    sales_rate,
    days_until_show,
    artist_tier,
    average_ticket_price,
    created_at,
    synced_at,
    ticket_sales_key,
    
    -- Additional calculated fields
    CASE 
        WHEN venue_capacity_clean > 0 THEN 
            ROUND((cumulative_tickets_sold::FLOAT / venue_capacity_clean::FLOAT) * 100, 2)
        ELSE NULL 
    END AS venue_utilization_pct,
    
    -- Sales velocity calculation using custom macro
    
    CASE 
        WHEN days_until_show > 0 THEN 
            ROUND(tickets_sold_clean::FLOAT / days_until_show::FLOAT, 2)
        ELSE 
            NULL 
    END
 AS sales_velocity_per_day
    
FROM cleaned_ticket_sales
    )
;


  