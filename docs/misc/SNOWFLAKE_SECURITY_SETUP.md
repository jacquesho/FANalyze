# Snowflake Security Setup Guide

## Overview

This guide walks you through setting up proper RBAC (Role-Based Access Control) in Snowflake for your FANalyze v2.0 project. This demonstrates data governance best practices and can help score extra points in your capstone evaluation.

## Why This Setup?

### ✅ **Service User (Required)**
- **Purpose**: Automated processes (dbt, Airflow, Python scripts)
- **Authentication**: Key-pair (no passwords)
- **Best Practice**: Separates automated processes from human users
- **Security**: Non-interactive, can't be used for manual logins

### ✅ **Human User (Recommended)**
- **Purpose**: Your day-to-day development work
- **Authentication**: Password + MFA (if enabled)
- **Best Practice**: Demonstrates least privilege principle
- **Why Not Just ACCOUNTADMIN?**
  - ACCOUNTADMIN has unlimited access (security risk)
  - Harder to audit what you did vs. what scripts did
  - Shows understanding of production-ready practices
  - Easier to demonstrate RBAC in demos

### ✅ **Roles with Least Privilege**
- **ROLE_ETL**: Full database access for transformations (includes CREATE permissions for dbt)
- **ROLE_ANALYST**: Read/write access for development (can create tables/views for ad-hoc analysis)
- **ROLE_READONLY**: Read-only for reporting/dashboards

## Step-by-Step Setup

### Step 1: Run the Setup Script

1. Log into Snowflake as **ACCOUNTADMIN**
2. Open the SQL worksheet
3. Edit `scripts/setup_snowflake_security.sql` and update if needed:
   - `WH_FANALYZE` - your warehouse name (default: WH_FANALYZE)
   - `FANALYZE` - your database name (default: FANALYZE)
4. Run the script

### Step 2: Configure the Service User's Public Key

After creating the service user, you need to add your public key:

```sql
ALTER USER USER_SVC SET RSA_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq5rbwVMP7UpKyJVK5WeJ
OVff2x/MM4d1ATJWPDcr73+XMxbF45AIFmah/P0ARGhItufEcvq2JD20G/9/tQjM
Vq/1mSN7NcUrQu4li4JNBxoPUxAHHfb5CSEE6Z3i0nGLbuQd0hXCa4ue5mJIL7Ou
7w7Br4E7ySq85alYe5+E1METdi2VEJ+h9jOtMFzQ9aX2PeELm+gCyH4AknSgPw3V
vayNJGalpKq5z48YUcG4KM+DYi+vyJm9PWbyeGJCUZrSlSUWLRR2421oyoULzpJx
PZtYnwVezGGMs8rKyzkdwIDQypnIZx4D9zKANwwbZveVonll7oemBO4jbp+L4NUl
5QIDAQAB
-----END PUBLIC KEY-----';
```

**Note**: Copy the entire content from your `rsa_key.pub` file, including the BEGIN/END lines.

### Step 3: Verify Key Setup

Check that the key was added correctly:

```sql
DESC USER USER_SVC;
```

Look for `RSA_PUBLIC_KEY_FP` - this should show a fingerprint.

### Step 4: Update Your Environment Variables

Update your `.env` file to use the service user:

```bash
# Snowflake Connection Settings
SNOWFLAKE_USER=USER_SVC
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_WAREHOUSE=WH_FANALYZE  # or your actual warehouse name
SNOWFLAKE_DATABASE=FANALYZE  # or your actual database name
SNOWFLAKE_SCHEMA=your_schema_name
SNOWFLAKE_ROLE=ROLE_ETL  # Changed from ACCOUNTADMIN

# Key Path (unchanged)
SNOWFLAKE_KEYPAIR_PATH=.secrets/rsa_key.p8
```

### Step 5: Test the Connection

Test your connection with the service user:

```python
from config.api_config import get_snowflake_connection

try:
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    
    # Check current user and role
    cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE()")
    user, role = cursor.fetchone()
    print(f"✅ Connected as {user} with role {role}")
    
    # Test a simple query
    cursor.execute("SELECT CURRENT_VERSION()")
    version = cursor.fetchone()[0]
    print(f"✅ Snowflake version: {version}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Step 6: (Optional) Set Up Human User

If you created `USER_DEV`:

1. Log out of ACCOUNTADMIN
2. Log in as `USER_DEV` with the temporary password (`ChangeMe123!`)
3. Change the password when prompted
4. Use this user for manual queries and exploration

## Security Best Practices Demonstrated

✅ **Separation of Concerns**: Service user for automation, human user for development  
✅ **Least Privilege**: Roles grant only necessary permissions  
✅ **Key-Pair Authentication**: More secure than passwords for automated processes  
✅ **Audit Trail**: Clear distinction between automated and manual actions  
✅ **Future Grants**: New objects automatically inherit permissions  

## For Your Capstone Demo

When presenting, highlight:

1. **"We use a service user with key-pair authentication for all automated processes"**
   - Shows understanding of production security practices
   - Demonstrates knowledge of M05/W02 concepts

2. **"We've implemented RBAC with least-privilege roles"**
   - Shows governance understanding
   - Can demonstrate different access levels

3. **"This setup allows us to audit who did what"**
   - Can show Access History queries
   - Demonstrates compliance awareness

## Troubleshooting

### "Access Denied" Errors
- Check that the role has been granted to the user
- Verify warehouse usage grants
- Ensure database/schema grants are correct

### "Invalid Key Pair"
- Verify the public key matches exactly (including line breaks)
- Check that you're using the correct user (USER_SVC)

### "Role Not Found"
- Make sure you've run the setup script completely
- Check that roles were created: `SHOW ROLES LIKE 'ROLE%'`

### "Insufficient privileges to operate on schema"
- Ensure CREATE SCHEMA permission is granted (should be included in the script)
- For dbt, the ETL role needs CREATE TABLE, CREATE VIEW, CREATE SCHEMA permissions

## Additional Security Features (Optional)

Consider implementing for extra credit:

1. **Data Masking Policies**: Mask PII columns based on role
2. **Row Access Policies**: Restrict rows based on user attributes
3. **Tags**: Classify data with sensitivity/owner tags
4. **Network Policies**: Restrict access by IP address

See `M05W02L03__lab_capstone_data_security.md` for examples.
