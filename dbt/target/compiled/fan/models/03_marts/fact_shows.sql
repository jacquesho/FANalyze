

with historical_shows as (
    select 
        show_id,
        artist_id,
        venue_id,
        show_date,
        show_year,
        show_month,
        show_quarter,
        day_of_week,
        season,
        city_name,
        state_code,
        country_name,
        market_size,
        venue_type,
        venue_capacity,
        tickets_sold,
        is_sellout,
        attendance_rate,
        calculated_attendance_rate,
        calculated_sellout,
        average_ticket_price,
        revenue,
        revenue_per_ticket,
        source,
        'Historical' as show_status,
        null as last_updated,
        current_timestamp as ingested_at
        
    from DB_T4.FAN_intermediate.int_shows
),

upcoming_shows as (
    select 
        show_id,
        null as artist_id,  -- Will be populated when artist data is available
        venue_id,
        show_date,
        extract(year from show_date) as show_year,
        extract(month from show_date) as show_month,
        extract(quarter from show_date) as show_quarter,
        extract(dayofweek from show_date) as day_of_week,
        case 
            when extract(month from show_date) in (12, 1, 2) then 'Winter'
            when extract(month from show_date) in (3, 4, 5) then 'Spring'
            when extract(month from show_date) in (6, 7, 8) then 'Summer'
            when extract(month from show_date) in (9, 10, 11) then 'Fall'
        end as season,
        city_name,
        state_code,
        country_name,
        null as market_size,  -- Will be populated based on venue
        null as venue_type,   -- Will be populated based on venue
        null as venue_capacity,  -- Will be populated based on venue
        null as tickets_sold,  -- Will be updated as sales data comes in
        null as is_sellout,    -- Will be updated as sales data comes in
        null as attendance_rate,  -- Will be updated as sales data comes in
        null as calculated_attendance_rate,
        null as calculated_sellout,
        null as average_ticket_price,  -- Will be updated as pricing data comes in
        null as revenue,  -- Will be updated as sales data comes in
        null as revenue_per_ticket,
        source,
        'Upcoming' as show_status,
        null as last_updated,
        collected_at as ingested_at
        
    from DB_T4.FAN_staging.stg_shows_future
),

unified_shows as (
    select * from historical_shows
    union all
    select * from upcoming_shows
)

select 
    show_id,
    artist_id,
    venue_id,
    show_date,
    show_year,
    show_month,
    show_quarter,
    day_of_week,
    season,
    city_name,
    state_code,
    country_name,
    market_size,
    venue_type,
    venue_capacity,
    tickets_sold,
    is_sellout,
    attendance_rate,
    calculated_attendance_rate,
    calculated_sellout,
    average_ticket_price,
    revenue,
    revenue_per_ticket,
    source,
    show_status,
    last_updated,
    ingested_at,
    
    -- Business metrics (only for historical shows with data)
    case 
        when show_status = 'Historical' and tickets_sold is not null then
            case 
                when tickets_sold >= venue_capacity * 0.9 then 'Near Sellout'
                when tickets_sold >= venue_capacity * 0.7 then 'Good Sales'
                when tickets_sold >= venue_capacity * 0.5 then 'Average Sales'
                else 'Low Sales'
            end
        else null
    end as sales_performance,
    
    case 
        when show_status = 'Historical' and revenue is not null then
            case 
                when revenue >= 1000000 then 'High Revenue'
                when revenue >= 500000 then 'Medium Revenue'
                when revenue >= 100000 then 'Low Revenue'
                else 'Very Low Revenue'
            end
        else null
    end as revenue_tier,
    
    -- Day of week performance
    case 
        when day_of_week in (6, 7) then 'Weekend'
        else 'Weekday'
    end as weekend_show,
    
    -- Time-based status
    case 
        when show_date < current_date then 'Past'
        when show_date = current_date then 'Today'
        when show_date <= current_date + interval '7 days' then 'This Week'
        when show_date <= current_date + interval '30 days' then 'This Month'
        when show_date <= current_date + interval '90 days' then 'Next 3 Months'
        else 'Future'
    end as time_status,
    
    -- Days until/from show
    case 
        when show_date < current_date then datediff(day, show_date, current_date)
        else datediff(day, current_date, show_date)
    end as days_from_show
    
from unified_shows