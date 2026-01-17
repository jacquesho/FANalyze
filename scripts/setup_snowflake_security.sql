-- ============================================================================
-- Snowflake Security Setup for FANalyze v2.0
-- ============================================================================
-- This script sets up proper RBAC with service users and roles
-- Run this as ACCOUNTADMIN in your new Snowflake account
-- ============================================================================

-- ============================================================================
-- STEP 1: Create Service User for Automated Processes
-- ============================================================================
-- This user will be used by dbt, Airflow, and Python scripts
-- Uses key-pair authentication (no password)

CREATE USER IF NOT EXISTS USER_SVC
  TYPE = SERVICE
  COMMENT = 'Service user for FANalyze automated pipelines (dbt, Airflow, scripts)';

-- Note: After creating the user, you'll need to set the public key:
-- ALTER USER USER_SVC SET RSA_PUBLIC_KEY='<your_public_key_content>';

-- ============================================================================
-- STEP 2: Create Human User (Optional but Recommended)
-- ============================================================================
-- This is for your day-to-day work - separate from ACCOUNTADMIN
-- You can use ACCOUNTADMIN for admin tasks, but use this for regular work

CREATE USER IF NOT EXISTS USER_DEV
  PASSWORD = 'ChangeMe123!'  -- Change this immediately after first login
  MUST_CHANGE_PASSWORD = TRUE
  COMMENT = 'Developer user for FANalyze project work';

-- ============================================================================
-- STEP 3: Create Roles with Least Privilege
-- ============================================================================

-- Role for ETL/Data Pipeline operations
CREATE ROLE IF NOT EXISTS ROLE_ETL;
GRANT ROLE ROLE_ETL TO USER USER_SVC;

-- Role for data analysts/developers
CREATE ROLE IF NOT EXISTS ROLE_ANALYST;
GRANT ROLE ROLE_ANALYST TO USER USER_DEV;

-- Role for read-only access (for reporting, dashboards)
CREATE ROLE IF NOT EXISTS ROLE_READONLY;

-- ============================================================================
-- STEP 4: Grant Warehouse Access
-- ============================================================================
-- Note: Update 'WH_FANALYZE' if your warehouse has a different name

-- Grant warehouse usage to ETL role (for dbt/scripts)
GRANT USAGE ON WAREHOUSE WH_FANALYZE TO ROLE ROLE_ETL;

-- Grant warehouse usage to analyst role
GRANT USAGE ON WAREHOUSE WH_FANALYZE TO ROLE ROLE_ANALYST;

-- Grant warehouse usage to readonly role
GRANT USAGE ON WAREHOUSE WH_FANALYZE TO ROLE ROLE_READONLY;

-- ============================================================================
-- STEP 5: Grant Database and Schema Access
-- ============================================================================
-- Note: Update 'FANALYZE' if your database has a different name

-- ETL Role: Full access to database (for dbt transformations)
-- Includes CREATE permissions needed for dbt to build models
GRANT USAGE ON DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT USAGE ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT CREATE SCHEMA ON DATABASE FANALYZE TO ROLE ROLE_ETL;  -- Needed for dbt to create schemas
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ETL;  -- Needed for dbt
GRANT SELECT ON ALL VIEWS IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT CREATE VIEW ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ETL;  -- Needed for dbt
GRANT USAGE ON ALL FUNCTIONS IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT CREATE FUNCTION ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ETL;  -- Optional for dbt macros
GRANT USAGE ON ALL PROCEDURES IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT CREATE PROCEDURE ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ETL;  -- Optional

-- Future grants for ETL role (so new objects are automatically accessible)
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT SELECT ON FUTURE VIEWS IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT USAGE ON FUTURE FUNCTIONS IN DATABASE FANALYZE TO ROLE ROLE_ETL;
GRANT USAGE ON FUTURE PROCEDURES IN DATABASE FANALYZE TO ROLE ROLE_ETL;

-- Analyst Role: Read and write access (can create tables/views for ad-hoc analysis)
GRANT USAGE ON DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT USAGE ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;  -- For ad-hoc analysis
GRANT SELECT ON ALL VIEWS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT CREATE VIEW ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;  -- For ad-hoc analysis
GRANT USAGE ON ALL FUNCTIONS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;

-- Future grants for analyst role
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT SELECT ON FUTURE VIEWS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;
GRANT USAGE ON FUTURE FUNCTIONS IN DATABASE FANALYZE TO ROLE ROLE_ANALYST;

-- Readonly Role: Read-only access
GRANT USAGE ON DATABASE FANALYZE TO ROLE ROLE_READONLY;
GRANT USAGE ON ALL SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_READONLY;
GRANT SELECT ON ALL TABLES IN DATABASE FANALYZE TO ROLE ROLE_READONLY;
GRANT SELECT ON ALL VIEWS IN DATABASE FANALYZE TO ROLE ROLE_READONLY;

-- Future grants for readonly role
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE FANALYZE TO ROLE ROLE_READONLY;
GRANT SELECT ON FUTURE TABLES IN DATABASE FANALYZE TO ROLE ROLE_READONLY;
GRANT SELECT ON FUTURE VIEWS IN DATABASE FANALYZE TO ROLE ROLE_READONLY;

-- ============================================================================
-- STEP 6: Set Default Roles
-- ============================================================================

-- Set default role for service user
ALTER USER USER_SVC SET DEFAULT_ROLE = ROLE_ETL;
ALTER USER USER_SVC SET DEFAULT_WAREHOUSE = WH_FANALYZE;

-- Set default role for dev user
ALTER USER USER_DEV SET DEFAULT_ROLE = ROLE_ANALYST;
ALTER USER USER_DEV SET DEFAULT_WAREHOUSE = WH_FANALYZE;

-- ============================================================================
-- STEP 7: Verify Setup
-- ============================================================================

-- Check users
SHOW USERS LIKE 'USER%';

-- Check roles
SHOW ROLES LIKE 'ROLE%';

-- Check grants for ETL role
SHOW GRANTS TO ROLE ROLE_ETL;

-- Check grants for analyst role
SHOW GRANTS TO ROLE ROLE_ANALYST;

-- Check grants for readonly role
SHOW GRANTS TO ROLE ROLE_READONLY;

-- ============================================================================
-- NEXT STEPS:
-- ============================================================================
-- 1. Set the public key for USER_SVC:
--    ALTER USER USER_SVC SET RSA_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
--    ...your public key content...
--    -----END PUBLIC KEY-----';
--
-- 2. Update your .env file to use USER_SVC:
--    SNOWFLAKE_USER=USER_SVC
--    SNOWFLAKE_ROLE=ROLE_ETL
--
-- 3. Test the connection with your Python scripts
--
-- 4. (Optional) Log in as USER_DEV and change the password
-- ============================================================================
