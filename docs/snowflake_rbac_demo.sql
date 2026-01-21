-- Snowflake RBAC Demonstration Query
-- Shows roles, users, role hierarchy, and privileges

-- 1. Role Hierarchy: Show all roles and their parent roles
SELECT
    r.role_name,
    r.role_owner,
    r.created_on,
    r.comment,
    r.is_default,
    r.is_current,
    r.is_inherited,
    r.assigned_to_users,
    r.granted_to_roles,
    r.granted_roles
FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES r
ORDER BY r.role_name;

-- 2. Users and their assigned roles
SELECT
    u.name AS user_name,
    u.email,
    u.created_on AS user_created_on,
    u.last_success_login,
    u.disabled,
    u.has_password,
    u.has_rsa_public_key,
    r.role AS assigned_role,
    r.granted_on,
    r.granted_by
FROM SNOWFLAKE.ACCOUNT_USAGE.USERS u
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS r
    ON u.name = r.grantee_name
WHERE r.privilege = 'USAGE'
    AND r.granted_on = 'ROLE'
ORDER BY u.name, r.role;

-- 3. Role-to-Role Grants (Role Hierarchy)
SELECT
    granted_role AS child_role,
    grantee_name AS parent_role,
    granted_by,
    granted_on
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE privilege = 'USAGE'
    AND granted_on = 'ROLE'
ORDER BY granted_role, grantee_name;

-- 4. Privileges granted to roles (Database, Schema, Table, etc.)
SELECT
    grantee_name AS role_name,
    granted_on AS object_type,
    name AS object_name,
    privilege,
    granted_by,
    granted_on_time
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE granted_on IN ('DATABASE', 'SCHEMA', 'TABLE', 'VIEW', 'WAREHOUSE')
ORDER BY grantee_name, granted_on, name, privilege;

-- 5. Comprehensive RBAC Summary View
WITH role_hierarchy AS (
    SELECT
        granted_role AS role_name,
        grantee_name AS parent_role,
        'ROLE' AS grant_type
    FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
    WHERE privilege = 'USAGE' AND granted_on = 'ROLE'
),
user_roles AS (
    SELECT
        grantee_name AS user_name,
        role AS role_name,
        'USER' AS grant_type
    FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
    WHERE privilege = 'USAGE' AND granted_on = 'ROLE'
)
SELECT
    'ROLE HIERARCHY' AS rbac_type,
    rh.role_name,
    rh.parent_role AS assigned_to,
    NULL AS privilege,
    NULL AS object_name
FROM role_hierarchy rh
UNION ALL
SELECT
    'USER ROLE ASSIGNMENT' AS rbac_type,
    ur.role_name,
    ur.user_name AS assigned_to,
    NULL AS privilege,
    NULL AS object_name
FROM user_roles ur
ORDER BY rbac_type, role_name, assigned_to;

-- 6. FANalyze-specific RBAC (filtered for your project)
SELECT
    grantee_name AS role_or_user,
    granted_on AS object_type,
    name AS object_name,
    privilege,
    CASE
        WHEN granted_on = 'DATABASE' THEN 'Database Access'
        WHEN granted_on = 'SCHEMA' THEN 'Schema Access'
        WHEN granted_on = 'TABLE' THEN 'Table Access'
        WHEN granted_on = 'VIEW' THEN 'View Access'
        WHEN granted_on = 'WAREHOUSE' THEN 'Warehouse Access'
        WHEN granted_on = 'ROLE' THEN 'Role Assignment'
        ELSE granted_on
    END AS access_type,
    granted_by,
    granted_on_time
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE name LIKE '%FANALYZE%' OR name LIKE '%FAN_%'
UNION ALL
SELECT
    grantee_name AS role_or_user,
    granted_on AS object_type,
    name AS object_name,
    privilege,
    CASE
        WHEN granted_on = 'DATABASE' THEN 'Database Access'
        WHEN granted_on = 'SCHEMA' THEN 'Schema Access'
        WHEN granted_on = 'TABLE' THEN 'Table Access'
        WHEN granted_on = 'VIEW' THEN 'View Access'
        WHEN granted_on = 'WAREHOUSE' THEN 'Warehouse Access'
        WHEN granted_on = 'ROLE' THEN 'Role Assignment'
        ELSE granted_on
    END AS access_type,
    granted_by,
    granted_on_time
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE name LIKE '%FANALYZE%' OR name LIKE '%FAN_%'
ORDER BY role_or_user, object_type, object_name, privilege;

-- 7. Current User's Effective Roles and Privileges
SELECT
    CURRENT_USER() AS current_user,
    CURRENT_ROLE() AS current_role,
    r.role_name,
    r.is_default,
    r.is_current,
    r.is_inherited
FROM TABLE(INFORMATION_SCHEMA.APPLICABLE_ROLES()) r
ORDER BY r.is_current DESC, r.is_inherited, r.role_name;
