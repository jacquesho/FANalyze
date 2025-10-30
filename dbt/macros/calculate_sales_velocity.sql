-- Custom macro: Calculate sales velocity per day
-- File: macros/calculate_sales_velocity.sql

{% macro calculate_sales_velocity(tickets_sold_column, days_until_show_column) %}
    {{ return(adapter.dispatch('calculate_sales_velocity', 'dbt')(tickets_sold_column, days_until_show_column)) }}
{% endmacro %}

{% macro default__calculate_sales_velocity(tickets_sold_column, days_until_show_column) %}
    CASE 
        WHEN {{ days_until_show_column }} > 0 THEN 
            ROUND({{ tickets_sold_column }}::FLOAT / {{ days_until_show_column }}::FLOAT, 2)
        ELSE 
            NULL 
    END
{% endmacro %}

{% macro snowflake__calculate_sales_velocity(tickets_sold_column, days_until_show_column) %}
    CASE 
        WHEN {{ days_until_show_column }} > 0 THEN 
            ROUND({{ tickets_sold_column }}::FLOAT / {{ days_until_show_column }}::FLOAT, 2)
        ELSE 
            NULL 
    END
{% endmacro %}
