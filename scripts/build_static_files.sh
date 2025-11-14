#!/usr/bin/env bash

# ============================================================================
# build_static_files.sh
#
# Builds the Docker image for FastAPI with embedded React components.
# The POSTGREST_URL is automatically read from the cluster-specific .env file.
#
# Usage: ./scripts/build_static_files.sh [cluster-name]
# Example: ./scripts/build_static_files.sh dev
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default to 'dev' cluster if not specified
CLUSTER_NAME="${1:-dev}"
ENV_FILE="$PROJECT_ROOT/.env.cluster-$CLUSTER_NAME"

# Validate cluster configuration exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Cluster configuration not found: $ENV_FILE"
  echo "Create a cluster first with: ./scripts/setup-cluster.sh create $CLUSTER_NAME"
  exit 1
fi

echo "Building Docker image for cluster: $CLUSTER_NAME"
echo "Using configuration: $ENV_FILE"
echo ""

# Build FastAPI Docker image with React components compiled in
# The multi-stage Dockerfile will:
# 1. Load .env.cluster-{CLUSTER_NAME} in webpack via CLUSTER_NAME build arg
# 2. Build React components with cluster-specific configuration
# 3. Copy built assets into Python image
cd "$PROJECT_ROOT"
CLUSTER_NAME="$CLUSTER_NAME" docker compose -f docker/docker-compose.yml --env-file "$ENV_FILE" build fastapi

if [ $? -eq 0 ]; then
  echo ""
  echo "✓ Docker image built successfully for cluster: $CLUSTER_NAME"
  exit 0
else
  echo ""
  echo "✗ Docker build failed for cluster: $CLUSTER_NAME"
  exit 1
fi
