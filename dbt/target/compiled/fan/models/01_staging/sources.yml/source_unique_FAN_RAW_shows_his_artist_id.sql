
    
    

select
    artist_id as unique_field,
    count(*) as n_records

from DB_T4.FAN_RAW.shows_his
where artist_id is not null
group by artist_id
having count(*) > 1


