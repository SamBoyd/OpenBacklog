# Use the official PostgreSQL image
# Consider pinning to a specific major version (e.g., postgres:16) for stability
FROM postgres:17

# Environment variables for database configuration
# These should be set during container runtime (e.g., via docker run -e or docker-compose.yml)
# - POSTGRES_USER: Username for the superuser (default: postgres)
# - POSTGRES_PASSWORD: Password for the superuser
# - POSTGRES_DB: Name for the default database to create
# Example runtime command:
# docker run -d \
#   --name my-postgres \
#   -e POSTGRES_PASSWORD=mysecretpassword \
#   -e POSTGRES_USER=myuser \
#   -e POSTGRES_DB=mydatabase \
#   -v postgres_data:/var/lib/postgresql/data \
#   -p 5432:5432 \
#   postgres:latest

# The official image handles setting up the database based on the environment variables.

# Expose the default PostgreSQL port
EXPOSE 5432

# Define the mount point for persistent data
# This volume should be mounted at runtime to persist data across container restarts.
VOLUME /var/lib/postgresql/data

# Healthcheck to verify PostgreSQL is ready (optional but recommended)
# This checks if the server is accepting connections for the default user/db
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 \
  CMD pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} || exit 1

# Note: For production environments, consider:
# - Pinning the base image version (e.g., postgres:16-alpine).
# - Using a more robust configuration management system than environment variables for secrets.
# - Configuring backups.
# - Tuning PostgreSQL performance settings via a custom postgresql.conf file copied into the image
#   or mounted at /docker-entrypoint-initdb.d/ for initialization scripts.
