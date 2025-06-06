{% macro is_weekend(date_column) %}
    CASE 
        WHEN EXTRACT(DOW FROM {{ date_column }}) IN (0, 6) THEN TRUE
        ELSE FALSE
    END
{% endmacro %}
