#!/bin/sh

# Redis initialization script for LiteLLM
# This script runs when the Redis container starts to set up LiteLLM-specific configuration

set -e
set -x
echo "Starting Redis initialization for LiteLLM..."

# Wait for Redis to be ready (simple check)
until redis-cli -a "${REDIS_PASSWORD}" ping > /dev/null 2>&1; do
  echo "Waiting for Redis to be ready..."
  sleep 1
done

echo "Redis is ready, setting up LiteLLM configuration..."

# Create additional users (optional - Redis 6+ supports ACL)
if [ -n "${REDIS_APP_USER}" ] && [ -n "${REDIS_APP_PASSWORD}" ]; then
  echo "Creating application user for LiteLLM..."
  redis-cli -a "${REDIS_PASSWORD}" ACL SETUSER "${REDIS_APP_USER}" on ">${REDIS_APP_PASSWORD}" "~*" "&*" "+@all"
fi

# Set up LiteLLM-specific configuration
echo "Setting up LiteLLM Redis configuration..."

# LiteLLM cache settings
redis-cli -a "${REDIS_PASSWORD}" SET "litellm:cache:enabled" "true"
redis-cli -a "${REDIS_PASSWORD}" SET "litellm:cache:ttl" "3600"
redis-cli -a "${REDIS_PASSWORD}" SET "litellm:cache:max_size" "1000"

# LiteLLM rate limiting settings
redis-cli -a "${REDIS_PASSWORD}" SET "litellm:rate_limit:enabled" "true"
redis-cli -a "${REDIS_PASSWORD}" SET "litellm:rate_limit:window" "60"
redis-cli -a "${REDIS_PASSWORD}" SET "litellm:rate_limit:max_requests" "100"

# Application metadata
redis-cli -a "${REDIS_PASSWORD}" SET "app:name" "taskmanagement"
redis-cli -a "${REDIS_PASSWORD}" SET "app:version" "1.0.0"
redis-cli -a "${REDIS_PASSWORD}" SET "app:startup_time" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "LiteLLM Redis initialization completed successfully!" 
