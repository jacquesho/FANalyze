# Update .env Configuration for user_fanalyze_ingest

## 🔧 **Step 1: Run the User Creation Script**

```bash
# Create the user_fanalyze_ingest user
uv run python scripts/database/create_ingest_user.py
```

## 🔧 **Step 2: Update Your .env File**

Add these lines to your existing `.env` file:

```bash
# Add these lines to your existing .env file
POSTGRES_USER_INGEST=user_fanalyze_ingest
POSTGRES_PASSWORD_INGEST=fanalyze_ingest_password
```

## 🔧 **Step 3: Your Complete .env Should Look Like**

```bash
# Your existing PostgreSQL configuration (keep these)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_existing_password

# Add the new ingest user configuration
POSTGRES_USER_INGEST=user_fanalyze_ingest
POSTGRES_PASSWORD_INGEST=fanalyze_ingest_password

# Your other existing configuration...
# (Snowflake, API keys, etc.)
```

## 🔧 **Step 4: Update CSV Loader to Use New User**

The CSV loader will automatically use the new user credentials when you run it.

## 🔧 **Step 5: Test the Setup**

```bash
# Test the CSV ingestion with the new user
uv run python tests/DB_tests/test_csv_ingestion.py
```

## 🎯 **Benefits of This Approach**

1. **Security** - Dedicated user for data ingestion
2. **Isolation** - Separate from your admin operations
3. **Permissions** - Only has access to staging schema
4. **Auditing** - Can track data ingestion operations
5. **Flexibility** - Can easily switch between users

## 🔧 **How It Works**

- **Your existing connection** - Used to create the new user
- **New user credentials** - Stored in .env for scripts to use
- **Automatic switching** - Scripts use the appropriate user for their purpose
- **Backward compatibility** - Your existing setup continues to work
