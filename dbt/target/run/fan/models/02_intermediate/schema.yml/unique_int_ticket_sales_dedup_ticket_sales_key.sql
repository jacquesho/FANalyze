
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    ticket_sales_key as unique_field,
    count(*) as n_records

from DB_T4.FAN_intermediate.int_ticket_sales_dedup
where ticket_sales_key is not null
group by ticket_sales_key
having count(*) > 1



  
  
      
    ) dbt_internal_test