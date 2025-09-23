#!/bin/bash

set -e

export PYTHONPATH='.' 
export ENVIRONMENT=test

# Variables
DB_USER="taskmanager_test_user"
DB_PASSWORD="securepassword123"
APP_DB="taskmanager_test_db"
POSTGREST_PASSWORD="securepassword123"

MEMORY_DB="memory_test_db"
MEMORY_DB_USER="memory_test_user"
MEMORY_DB_PASSWORD="securepassword123"

POSTGREST_AUTHENTICATOR_ROLE="test_authenticator"
POSTGREST_ANONYMOUS_ROLE="test_anonymous"
POSTGREST_AUTHENTICATED_ROLE="test_authenticated"

PUBLIC_SCHEMA="dev"
PRIVATE_SCHEMA="private"

MAX_DB_INDEX=20

## --- Create the database and roles ---
# Drop databases if they exist
psql postgres -c "DROP DATABASE IF EXISTS $APP_DB;"
psql postgres -c "DROP DATABASE IF EXISTS $MEMORY_DB;"
for i in $(seq 0 $MAX_DB_INDEX); do
    numbered_db="${APP_DB}_$(printf "%02d" $i)"
    psql postgres -c "DROP DATABASE IF EXISTS $numbered_db;"
done

# Drop roles if they exist
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_AUTHENTICATOR_ROLE;"
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_ANONYMOUS_ROLE;"
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_AUTHENTICATED_ROLE;"

## --- Create the database and roles ---
# Create user if it doesn't exist
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$MEMORY_DB_USER'" | grep -q 1 || psql postgres -c "CREATE USER $MEMORY_DB_USER WITH PASSWORD '$MEMORY_DB_PASSWORD';"

# Create roles
psql postgres -c "CREATE ROLE $POSTGREST_AUTHENTICATOR_ROLE NOINHERIT NOCREATEDB NOCREATEROLE NOSUPERUSER LOGIN password '$POSTGREST_PASSWORD';"
psql postgres -c "CREATE ROLE $POSTGREST_ANONYMOUS_ROLE NOLOGIN;"
psql postgres -c "CREATE ROLE $POSTGREST_AUTHENTICATED_ROLE NOLOGIN;"

# Grant permissions to create roles and grant admin on the postgrest roles to the test user
psql postgres -c "ALTER USER $DB_USER CREATEROLE;"
psql postgres -c "GRANT $POSTGREST_ANONYMOUS_ROLE TO $DB_USER WITH ADMIN OPTION;"
psql postgres -c "GRANT $POSTGREST_AUTHENTICATED_ROLE TO $DB_USER WITH ADMIN OPTION;"
psql postgres -c "GRANT $POSTGREST_AUTHENTICATOR_ROLE TO $DB_USER WITH ADMIN OPTION;"
 
# Create databases
psql postgres -c "CREATE DATABASE $APP_DB OWNER $DB_USER;"
psql postgres -c "CREATE DATABASE $MEMORY_DB OWNER $MEMORY_DB_USER;"

# Create schema private
psql -d $APP_DB -c "CREATE SCHEMA $PRIVATE_SCHEMA AUTHORIZATION $DB_USER;"

# Grant permissions
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $APP_DB TO $DB_USER;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $MEMORY_DB TO $MEMORY_DB_USER;"

# Run the migrations
alembic upgrade head

# Create user for the ReactJs hook integration tests
psql taskmanager_test_db -c "INSERT INTO private.users (
    id,
    email,
    name,
    hashed_password,
    is_active,
    is_superuser,
    is_verified,
    last_logged_in,
    profile_picture_url,
    display_preferences
) VALUES (
    '6c3dd9da-2698-46b5-a8ec-45225579305d',
    'test@example.com',
    'Testiquito Test',
    '$argon2id$v=19$m=65536,t=3,p=4$pT4DCSH+6ZIb1yfuGx2fpw$8m8s3wJYGkis1A+Ex5gE3q1mlNZtmUHNu2FTHOjRFhM',
    true,
    false,
    true,
    NOW(),
    'bba9772a974ac6a9220be9fce9f25ff9.png',
    '{}'::jsonb
);"

psql taskmanager_test_db -c "INSERT INTO private.oauth_account (
    id,
    user_id,
    oauth_name,
    access_token,
    expires_at,
    refresh_token,
    account_id,
    account_email
) VALUES (
    '6c3dd9da-2698-46b5-a8ec-452255793999',
    '6c3dd9da-2698-46b5-a8ec-45225579305d',
    'google-oauth2',
    'example_access_token_string', 
    EXTRACT(EPOCH FROM NOW() + INTERVAL '1 hour')::integer, 
    'example_refresh_token_string', 
    'google-oauth2|100049631933995708445', 
    'test@example.com'
);"

psql taskmanager_test_db -c "INSERT INTO dev.workspace (
    id,
    name,
    description,
    icon,
    user_id
) VALUES (
    '5f8a85c0-5974-4444-9875-ae5c56014fee',
    'Test Workspace',
    'This is a test workspace',
    'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
    '6c3dd9da-2698-46b5-a8ec-45225579305d'
);"
