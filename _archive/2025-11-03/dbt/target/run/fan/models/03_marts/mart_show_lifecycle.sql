
  
    

create or replace transient table DB_T4.FAN_marts.mart_show_lifecycle
    
    
    
    as (

with show_lifecycle as (
    select 
        fs.show_id,
        fs.artist_id,
        fs.venue_id,
        fs.show_date,
        fs.show_status,
        fs.time_status,
        fs.days_from_show,
        fs.tickets_sold,
        fs.revenue,
        fs.attendance_rate,
        fs.is_sellout,
        
        -- Lifecycle tracking
        case 
            when fs.show_date < current_date and fs.show_status = 'Upcoming' then 'Needs Status Update'
            when fs.show_date >= current_date and fs.show_status = 'Historical' then 'Needs Status Update'
            else 'Status Current'
        end as status_consistency,
        
        -- Data completeness for upcoming shows
        case 
            when fs.show_status = 'Upcoming' then
                case 
                    when fs.tickets_sold is not null and fs.revenue is not null then 'Complete'
                    when fs.tickets_sold is not null or fs.revenue is not null then 'Partial'
                    else 'Basic'
                end
            else 'Historical'
        end as data_completeness,
        
        -- Update priority
        case 
            when fs.show_date < current_date and fs.show_status = 'Upcoming' then 'High'
            when fs.show_date <= current_date + interval '7 days' and fs.tickets_sold is null then 'Medium'
            when fs.show_date <= current_date + interval '30 days' and fs.tickets_sold is null then 'Low'
            else 'None'
        end as update_priority
        
    from DB_T4.FAN_marts.fact_shows fs
),

venue_artist_matching as (
    -- Try to match upcoming shows with historical artist data
    select 
        fs.show_id,
        da.artist_id,
        da.artist_name,
        da.artist_tier
    from DB_T4.FAN_marts.fact_shows fs
    left join DB_T4.FAN_marts.dim_artists da on fs.artist_id = da.artist_id
    where fs.show_status = 'Upcoming'
      and fs.artist_id is null
)

select 
    sl.show_id,
    sl.artist_id,
    sl.venue_id,
    sl.show_date,
    sl.show_status,
    sl.time_status,
    sl.days_from_show,
    sl.tickets_sold,
    sl.revenue,
    sl.attendance_rate,
    sl.is_sellout,
    sl.status_consistency,
    sl.data_completeness,
    sl.update_priority,
    
    -- Artist matching
    vam.artist_name,
    vam.artist_tier,
    
    -- Action required
    case 
        when sl.status_consistency = 'Needs Status Update' then 'Update Status'
        when sl.update_priority = 'High' then 'Urgent Data Update'
        when sl.update_priority = 'Medium' then 'Schedule Data Update'
        when sl.data_completeness = 'Basic' then 'Enhance Data'
        else 'Monitor'
    end as recommended_action
    
from show_lifecycle sl
left join venue_artist_matching vam on sl.show_id = vam.show_id
    )
;


  