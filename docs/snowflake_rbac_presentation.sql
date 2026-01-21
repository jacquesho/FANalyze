-- Snowflake RBAC Presentation Query
-- Single comprehensive query showing roles, users, and access

SELECT
    -- Role Information
    COALESCE(gr.grantee_name, gu.grantee_name) AS role_or_user,
    CASE
        WHEN gr.grantee_name IS NOT NULL THEN 'ROLE'
        WHEN gu.grantee_name IS NOT NULL THEN 'USER'
    END AS entity_type,
    
    -- What they have access to
    COALESCE(gr.granted_on, gu.granted_on) AS object_type,
    COALESCE(gr.name, gu.name) AS object_name,
    COALESCE(gr.privilege, gu.privilege) AS privilege,
    
    -- Context
    CASE
        WHEN COALESCE(gr.granted_on, gu.granted_on) = 'ROLE' THEN 'Role Assignment'
        WHEN COALESCE(gr.granted_on, gu.granted_on) = 'DATABASE' THEN 'Database Access'
        WHEN COALESCE(gr.granted_on, gu.granted_on) = 'SCHEMA' THEN 'Schema Access'
        WHEN COALESCE(gr.granted_on, gu.granted_on) = 'TABLE' THEN 'Table Access'
        WHEN COALESCE(gr.granted_on, gu.granted_on) = 'VIEW' THEN 'View Access'
        WHEN COALESCE(gr.granted_on, gu.granted_on) = 'WAREHOUSE' THEN 'Warehouse Access'
        ELSE COALESCE(gr.granted_on, gu.granted_on)
    END AS access_type,
    
    -- Metadata
    COALESCE(gr.granted_by, gu.granted_by) AS granted_by,
    COALESCE(gr.granted_on_time, gu.granted_on_time) AS granted_on_time

FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES gr
FULL OUTER JOIN SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS gu
    ON gr.grantee_name = gu.grantee_name
    AND gr.granted_on = gu.granted_on
    AND gr.name = gu.name
    AND gr.privilege = gu.privilege

WHERE
    -- Filter for FANalyze-related objects (adjust as needed)
    (
        COALESCE(gr.name, gu.name) LIKE '%FANALYZE%'
        OR COALESCE(gr.name, gu.name) LIKE '%FAN_%'
        OR COALESCE(gr.grantee_name, gu.grantee_name) LIKE '%FANALYZE%'
        OR COALESCE(gr.grantee_name, gu.grantee_name) LIKE '%ETL%'
        OR COALESCE(gr.grantee_name, gu.grantee_name) LIKE '%ANALYST%'
    )
    OR COALESCE(gr.granted_on, gu.granted_on) = 'ROLE'  -- Include all role assignments

ORDER BY
    entity_type,
    role_or_user,
    object_type,
    object_name,
    privilege;

-- Alternative: Simple Role Hierarchy View
SELECT
    'Role Hierarchy' AS rbac_component,
    granted_role AS role_name,
    grantee_name AS inherits_from_role,
    'Role-to-Role Grant' AS grant_type
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE privilege = 'USAGE' AND granted_on = 'ROLE'
ORDER BY granted_role, grantee_name;

-- Alternative: User Role Assignments
SELECT
    'User Role Assignment' AS rbac_component,
    grantee_name AS user_name,
    role AS assigned_role,
    'User-to-Role Grant' AS grant_type,
    granted_by,
    granted_on_time
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE privilege = 'USAGE' AND granted_on = 'ROLE'
ORDER BY grantee_name, role;
