#!/bin/bash

set -e

# Variables
DB_USER="taskmanager_user"
DB_PASSWORD="securepassword123"
APP_DB="taskmanager_db"
POSTGREST_PASSWORD="securepassword123"

MEMORY_DB="memory_db"
MEMORY_DB_USER="memory_user"
MEMORY_DB_PASSWORD="securepassword123"

POSTGREST_AUTHENTICATOR_ROLE="authenticator"
POSTGREST_ANONYMOUS_ROLE="anonymous"
POSTGREST_AUTHENTICATED_ROLE="authenticated"

PUBLIC_SCHEMA="dev"
PRIVATE_SCHEMA="private"


## --- Create the database and roles ---
# Drop databases if they exist
psql postgres -c "DROP DATABASE IF EXISTS $APP_DB;"
psql postgres -c "DROP DATABASE IF EXISTS $MEMORY_DB;"

# Drop roles if they exist
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_AUTHENTICATOR_ROLE;"
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_ANONYMOUS_ROLE;"
psql postgres -c "DROP ROLE IF EXISTS $POSTGREST_AUTHENTICATED_ROLE;"

## --- Create the database and roles ---
# Create user if it doesn't exist
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$MEMORY_DB_USER'" | grep -q 1 || psql postgres -c "CREATE USER $MEMORY_DB_USER WITH PASSWORD '$MEMORY_DB_PASSWORD';"

# grant permissions to create roles
psql postgres -c "ALTER USER $DB_USER CREATEROLE"
 
# Create databases
psql postgres -c "CREATE DATABASE $APP_DB OWNER $DB_USER;"
psql postgres -c "CREATE DATABASE $MEMORY_DB OWNER $MEMORY_DB_USER;"

# Create schema private
psql -d $APP_DB -c "CREATE SCHEMA $PRIVATE_SCHEMA AUTHORIZATION $DB_USER;"

# Grant permissions
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $APP_DB TO $DB_USER;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $MEMORY_DB TO $MEMORY_DB_USER;"

