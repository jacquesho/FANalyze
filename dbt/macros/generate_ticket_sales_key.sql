-- Custom macro: Generate unique ticket sales key
-- File: macros/generate_ticket_sales_key.sql

{% macro generate_ticket_sales_key(show_id_column, timestamp_column) %}
    {{ return(adapter.dispatch('generate_ticket_sales_key', 'dbt')(show_id_column, timestamp_column)) }}
{% endmacro %}

{% macro default__generate_ticket_sales_key(show_id_column, timestamp_column) %}
    MD5(CONCAT({{ show_id_column }}, '|', {{ timestamp_column }}))
{% endmacro %}

{% macro snowflake__generate_ticket_sales_key(show_id_column, timestamp_column) %}
    MD5(CONCAT({{ show_id_column }}, '|', {{ timestamp_column }}))
{% endmacro %}
