#!/bin/sh

set -e

# Substitute environment variables in Redis config
envsubst < /usr/local/etc/redis/redis.conf > /tmp/redis.conf

# Start Redis server in background
redis-server /tmp/redis.conf &
REDIS_PID=$!
echo "Redis started with PID: $REDIS_PID"

# Wait a moment for Redis to start
sleep 2

# Run initialization script
sh /usr/local/bin/redis-init.sh

# Keep container running
wait $REDIS_PID 