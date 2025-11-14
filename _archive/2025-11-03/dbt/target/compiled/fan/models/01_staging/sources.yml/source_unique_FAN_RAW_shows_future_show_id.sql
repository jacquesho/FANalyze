
    
    

select
    show_id as unique_field,
    count(*) as n_records

from DB_T4.FAN_RAW.shows_future
where show_id is not null
group by show_id
having count(*) > 1


