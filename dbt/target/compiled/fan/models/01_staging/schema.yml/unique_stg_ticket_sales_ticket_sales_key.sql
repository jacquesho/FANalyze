
    
    

select
    ticket_sales_key as unique_field,
    count(*) as n_records

from DB_T4.FAN_fan_staging.stg_ticket_sales
where ticket_sales_key is not null
group by ticket_sales_key
having count(*) > 1


