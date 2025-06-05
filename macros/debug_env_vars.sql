{% macro debug_env_vars() %}
    {% do log("SF_USER: " ~ env_var("SF_USER", "missing"), info=True) %}
    {% do log("SF_ROLE: " ~ env_var("SF_ROLE", "missing"), info=True) %}
    {% do log("SF_DATABASE: " ~ env_var("SF_DATABASE", "missing"), info=True) %}
    {% do log("SF_WAREHOUSE: " ~ env_var("SF_WAREHOUSE", "missing"), info=True) %}
    {% do log("SF_SCHEMA: " ~ env_var("SF_SCHEMA", "missing"), info=True) %}
{% endmacro %}
