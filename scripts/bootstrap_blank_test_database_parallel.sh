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

# Number of parallel databases to create (00-20)
MAX_DB_INDEX=20

# Create logs directory
mkdir -p ./bootstrap

# Logging functions
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_step() {
    echo "[STEP] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to create a single numbered database
create_numbered_database() {
    local db_index=$1
    local numbered_db="${APP_DB}_$(printf "%02d" $db_index)"
    local db_user="${DB_USER}"
    local log_file="./bootstrap/${numbered_db}.log"
    
    log_step "Creating database: $numbered_db"
    
    # Drop database if it exists
    psql postgres -c "DROP DATABASE IF EXISTS $numbered_db;" >> "$log_file" 2>&1 || true
    
    # Create user if it doesn't exist
    # psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'" | grep -q 1 || psql postgres -c "CREATE USER $db_user WITH PASSWORD '$DB_PASSWORD';" >> "$log_file" 2>&1
    
    # Create database
    psql postgres -c "CREATE DATABASE $numbered_db OWNER $db_user;" >> "$log_file" 2>&1
    
    # Create schema private
    psql -d $numbered_db -c "CREATE SCHEMA $PRIVATE_SCHEMA AUTHORIZATION $db_user;" >> "$log_file" 2>&1
    
    # Grant permissions
    psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $numbered_db TO $db_user;" >> "$log_file" 2>&1
    
    # Run migrations on the numbered database
    # Override the database_url for this specific database
    log_step "Running migrations on $numbered_db"
    DATABASE_URL="postgresql://taskmanager_test_user:securepassword123@localhost/${numbered_db}" \
    ASYNC_DATABASE_URL="postgresql+asyncpg://taskmanager_test_user:securepassword123@localhost/${numbered_db}" \
    DATABASE_NAME="$numbered_db" \
    DATABASE_APP_USER_USERNAME="$db_user" \
    PGDATABASE=$numbered_db alembic upgrade head >> "$log_file" 2>&1
    
    # Check if migrations were successful
    if [ $? -eq 0 ]; then
        log_success "Completed database: $numbered_db"
    else
        log_error "Failed to create database: $numbered_db (check $log_file for details)"
        return 1
    fi
}

log_info "Starting parallel test database creation..."

## --- Wipe log files ---
rm -f ./bootstrap/*.log

## --- Create the main database first ---
log_step "Creating main test database: $APP_DB"
main_log_file="./bootstrap/${APP_DB}.log"

# Drop databases if they exist
log_step "Dropping existing databases..."
psql postgres -c "DROP DATABASE IF EXISTS $APP_DB;" >> "$main_log_file" 2>&1
for i in $(seq 0 $MAX_DB_INDEX); do
    numbered_db="${APP_DB}_$(printf "%02d" $i)"
    psql postgres -c "DROP DATABASE IF EXISTS $numbered_db;" >> "$main_log_file" 2>&1
done
psql postgres -c "DROP DATABASE IF EXISTS $MEMORY_DB;" >> "$main_log_file" 2>&1

# Drop roles if they exist
log_step "Dropping existing roles..."
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_AUTHENTICATOR_ROLE;" >> "$main_log_file" 2>&1
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_ANONYMOUS_ROLE;" >> "$main_log_file" 2>&1
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_AUTHENTICATED_ROLE;" >> "$main_log_file" 2>&1

# Create user if it doesn't exist
log_step "Creating database users..."
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" >> "$main_log_file" 2>&1
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$MEMORY_DB_USER'" | grep -q 1 || psql postgres -c "CREATE USER $MEMORY_DB_USER WITH PASSWORD '$MEMORY_DB_PASSWORD';" >> "$main_log_file" 2>&1

# Create roles
psql postgres -c "CREATE ROLE $POSTGREST_AUTHENTICATOR_ROLE NOINHERIT NOCREATEDB NOCREATEROLE NOSUPERUSER LOGIN password '$POSTGREST_PASSWORD';" >> "$main_log_file" 2>&1
psql postgres -c "CREATE ROLE $POSTGREST_ANONYMOUS_ROLE NOLOGIN;" >> "$main_log_file" 2>&1
psql postgres -c "CREATE ROLE $POSTGREST_AUTHENTICATED_ROLE NOLOGIN;" >> "$main_log_file" 2>&1

# Grant permissions to create roles
psql postgres -c "ALTER USER $DB_USER SUPERUSER" >> "$main_log_file" 2>&1
 
# Create databases
log_step "Creating main databases..."
psql postgres -c "CREATE DATABASE $APP_DB OWNER $DB_USER;" >> "$main_log_file" 2>&1
psql postgres -c "CREATE DATABASE $MEMORY_DB OWNER $MEMORY_DB_USER;" >> "$main_log_file" 2>&1

# Create schema private
psql -d $APP_DB -c "CREATE SCHEMA $PRIVATE_SCHEMA AUTHORIZATION $DB_USER;" >> "$main_log_file" 2>&1

# Grant permissions
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $APP_DB TO $DB_USER;" >> "$main_log_file" 2>&1
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $MEMORY_DB TO $MEMORY_DB_USER;" >> "$main_log_file" 2>&1

# Run the migrations on main database
log_step "Running migrations on main database..."
alembic upgrade head >> "$main_log_file" 2>&1

# Check if migrations were successful
if [ $? -ne 0 ]; then
    log_error "Failed to run migrations on main database (check $main_log_file for details)"
    exit 1
fi

# Create user for the ReactJs hook integration tests
log_step "Setting up test user data..."
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
    '\$argon2id\$v=19\$m=65536,t=3,p=4\$pT4DCSH+6ZIb1yfuGx2fpw\$8m8s3wJYGkis1A+Ex5gE3q1mlNZtmUHNu2FTHOjRFhM',
    true,
    false,
    true,
    NOW(),
    'bba9772a974ac6a9220be9fce9f25ff9.png',
    '{}'::jsonb
);" >> "$main_log_file" 2>&1

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
);" >> "$main_log_file" 2>&1

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
);" >> "$main_log_file" 2>&1

log_success "Main database $APP_DB created successfully!"

## --- Create numbered databases ---
log_info "Creating numbered databases (00-$MAX_DB_INDEX)..."

# Start database creation
for i in $(seq 0 $MAX_DB_INDEX); do
    create_numbered_database $i
done

log_success "All databases created successfully!"
log_info "Created databases:"
echo "  - $APP_DB (main)"
echo "  - $MEMORY_DB (memory)"
for i in $(seq 0 $MAX_DB_INDEX); do
    echo "  - ${APP_DB}_$(printf "%02d" $i)"
done

log_info "Log files saved to ./bootstrap/ directory"
log_success "Parallel test database setup complete!" 