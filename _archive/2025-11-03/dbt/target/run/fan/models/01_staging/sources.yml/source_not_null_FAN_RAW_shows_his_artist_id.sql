
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select artist_id
from DB_T4.FAN_RAW.shows_his
where artist_id is null



  
  
      
    ) dbt_internal_test