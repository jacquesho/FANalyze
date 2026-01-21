-- RBAC Demonstration Query
-- Shows users (USER_SVC, USER_DEV) and roles (ROLE_ETL, ROLE_ANALYST, ROLE_READONLY)
-- Demonstrates access levels and role assignments

-- 1. User to Role Assignments (Who has what role)
SELECT
    grantee_name AS user_name,
    role AS assigned_role,
    'User → Role Assignment' AS access_level
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE deleted_on IS NULL
    AND grantee_name IN ('USER_SVC', 'USER_DEV')
    AND role IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
ORDER BY grantee_name, role;

-- 2. Role Hierarchy (Which roles inherit from other roles)
SELECT
    grantee_name AS child_role,
    name AS parent_role,
    'Role → Role Inheritance' AS access_level
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE privilege = 'USAGE'
    AND granted_on = 'ROLE'
    AND grantee_name IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
ORDER BY grantee_name, name;

-- 3. Role Privileges on Objects (What each role can access)
SELECT
    grantee_name AS role_name,
    granted_on AS object_type,
    name AS object_name,
    privilege,
    'Role → Object Privilege' AS access_level
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE grantee_name IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
    AND granted_on IN ('DATABASE', 'SCHEMA', 'TABLE', 'VIEW', 'WAREHOUSE')
ORDER BY grantee_name, granted_on, name, privilege;

-- 4. Complete RBAC Chain (User → Role → Object)
-- Shows the full access path: which users can access which objects through their roles
WITH user_roles AS (
    SELECT
        grantee_name AS user_name,
        role AS role_name
    FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
    WHERE deleted_on IS NULL
        AND grantee_name IN ('USER_SVC', 'USER_DEV')
        AND role IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
),
role_privileges AS (
    SELECT
        grantee_name AS role_name,
        granted_on AS object_type,
        name AS object_name,
        privilege
    FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
    WHERE grantee_name IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
        AND granted_on IN ('DATABASE', 'SCHEMA', 'TABLE', 'VIEW', 'WAREHOUSE')
)
SELECT
    ur.user_name,
    ur.role_name,
    rp.object_type,
    rp.object_name,
    rp.privilege,
    'User → Role → Object' AS access_level
FROM user_roles ur
INNER JOIN role_privileges rp ON ur.role_name = rp.role_name
ORDER BY ur.user_name, ur.role_name, rp.object_type, rp.object_name;

-- 5. Role Privilege Summary (Count by Privilege Type)
-- Easy-to-read summary showing access levels for each role
SELECT
    grantee_name AS role_name,
    COUNT(CASE WHEN privilege = 'USAGE' THEN 1 END) AS usage_count,
    COUNT(CASE WHEN privilege = 'SELECT' THEN 1 END) AS select_count,
    COUNT(CASE WHEN privilege = 'INSERT' THEN 1 END) AS insert_count,
    COUNT(CASE WHEN privilege = 'UPDATE' THEN 1 END) AS update_count,
    COUNT(CASE WHEN privilege = 'DELETE' THEN 1 END) AS delete_count,
    COUNT(CASE WHEN privilege = 'OWNERSHIP' THEN 1 END) AS ownership_count,
    COUNT(CASE WHEN privilege LIKE 'CREATE%' THEN 1 END) AS create_count,
    COUNT(CASE WHEN privilege = 'CREATE TABLE' THEN 1 END) AS create_table_count,
    COUNT(CASE WHEN privilege = 'CREATE VIEW' THEN 1 END) AS create_view_count,
    COUNT(CASE WHEN privilege = 'CREATE SCHEMA' THEN 1 END) AS create_schema_count,
    COUNT(*) AS total_privileges
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE grantee_name IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
    AND granted_on IN ('DATABASE', 'SCHEMA', 'TABLE', 'VIEW', 'WAREHOUSE')
GROUP BY grantee_name
ORDER BY grantee_name;

-- 6. Role Privilege Summary by Object Type
-- Shows privilege counts broken down by object type for each role
SELECT
    grantee_name AS role_name,
    granted_on AS object_type,
    COUNT(CASE WHEN privilege = 'USAGE' THEN 1 END) AS usage_count,
    COUNT(CASE WHEN privilege = 'SELECT' THEN 1 END) AS select_count,
    COUNT(CASE WHEN privilege = 'INSERT' THEN 1 END) AS insert_count,
    COUNT(CASE WHEN privilege = 'UPDATE' THEN 1 END) AS update_count,
    COUNT(CASE WHEN privilege = 'DELETE' THEN 1 END) AS delete_count,
    COUNT(CASE WHEN privilege = 'OWNERSHIP' THEN 1 END) AS ownership_count,
    COUNT(CASE WHEN privilege LIKE 'CREATE%' THEN 1 END) AS create_count,
    COUNT(*) AS total_privileges
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE grantee_name IN ('ROLE_ETL', 'ROLE_ANALYST', 'ROLE_READONLY')
    AND granted_on IN ('DATABASE', 'SCHEMA', 'TABLE', 'VIEW', 'WAREHOUSE')
GROUP BY grantee_name, granted_on
ORDER BY grantee_name, granted_on;
