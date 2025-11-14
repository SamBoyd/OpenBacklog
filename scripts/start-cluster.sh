#!/bin/bash

##############################################################################
# start-cluster.sh
#
# Starts a specific cluster using docker-compose
#
# Usage: ./scripts/start-cluster.sh <cluster-name>
# Example: ./scripts/start-cluster.sh dev
#
##############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

##############################################################################
# Functions
##############################################################################

print_error() {
  echo -e "${RED}Error: $1${NC}" >&2
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
  echo -e "${CYAN}ℹ $1${NC}"
}

print_header() {
  echo -e "${BLUE}=== Starting Cluster ===${NC}\n"
}

show_usage() {
  cat << EOF
${BLUE}Usage: ./scripts/start-cluster.sh <cluster-name>${NC}

${YELLOW}Arguments:${NC}
  <cluster-name>  Name of the cluster to start (e.g., 'dev', 'agent-1')

${YELLOW}Examples:${NC}
  ./scripts/start-cluster.sh dev
  ./scripts/start-cluster.sh agent-1

${YELLOW}Available clusters:${NC}
EOF
  find "$PROJECT_ROOT" -maxdepth 1 -name ".env.cluster-*" -type f -printf '%f\n' 2>/dev/null | \
    sed 's/^\.env\.cluster-/  - /' || echo "  (none configured)"
}

check_docker() {
  if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
  fi
}

validate_cluster() {
  local cluster_name=$1
  local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

  if [ ! -f "$env_file" ]; then
    print_error "Cluster '$cluster_name' not found. Configuration file missing: $env_file"
    echo ""
    show_usage
    exit 1
  fi
}

get_value_from_env() {
  local env_file=$1
  local var_name=$2

  if [ -f "$env_file" ]; then
    grep "^${var_name}=" "$env_file" | cut -d'=' -f2 | tr -d ' ' || echo ""
  fi
}

wait_for_health() {
  local cluster_name=$1
  local max_attempts=60
  local attempt=0

  echo ""
  print_info "Waiting for cluster to be healthy..."

  while [ $attempt -lt $max_attempts ]; do
    # Check if key services are running
    local running=$(CLUSTER_NAME="$cluster_name" docker-compose -f docker/docker-compose.yml --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps 2>/dev/null | grep -c " Up " || true)

    if [ "$running" -gt 0 ]; then
      print_success "Cluster is running"
      return 0
    fi

    echo -n "."
    sleep 1
    ((attempt++))
  done

  print_error "Cluster failed to start within timeout period"
  return 1
}

show_cluster_info() {
  local cluster_name=$1
  local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

  local fastapi_port=$(get_value_from_env "$env_file" "FASTAPI_PORT")
  local postgrest_port=$(get_value_from_env "$env_file" "POSTGREST_PORT")
  local postgres_port=$(get_value_from_env "$env_file" "POSTGRES_PORT")
  local app_domain=$(get_value_from_env "$env_file" "APP_DOMAIN")

  echo ""
  echo -e "${GREEN}=== Cluster Access Information ===${NC}"

  if [ -n "$app_domain" ] && [ "$app_domain" != "localhost" ]; then
    print_info "FastAPI:       http://${app_domain}:${fastapi_port}"
  else
    print_info "FastAPI:       http://localhost:${fastapi_port}"
  fi

  print_info "PostgREST:     http://localhost:${postgrest_port} (internal)"
  print_info "Database:      localhost:${postgres_port}"
  print_info "Cluster:       $cluster_name"
  echo ""
  print_info "View logs:     ./scripts/logs-cluster.sh $cluster_name"
  print_info "Stop cluster:  ./scripts/stop-cluster.sh $cluster_name"
}

##############################################################################
# Main
##############################################################################

main() {
  local cluster_name=$1

  # Validate arguments
  if [ -z "$cluster_name" ]; then
    print_error "Cluster name is required"
    echo ""
    show_usage
    exit 1
  fi

  if [ "$cluster_name" = "--help" ] || [ "$cluster_name" = "-h" ]; then
    show_usage
    exit 0
  fi

  print_header

  # Pre-flight checks
  check_docker
  validate_cluster "$cluster_name"

  local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

  print_info "Starting cluster: $cluster_name"
  print_info "Using environment: $env_file"
  echo ""

  # Build the Docker image with cluster-specific POSTGREST_URL from .env
  print_info "Building Docker image for cluster: $cluster_name..."
  if ! "$SCRIPT_DIR/build_static_files.sh" "$cluster_name"; then
    print_error "Failed to build Docker image for cluster"
    exit 1
  fi
  echo ""

  # Start the cluster (image is already built)
  print_info "Starting Docker Compose services..."
  cd "$PROJECT_ROOT"
  echo "CLUSTER_NAME=$cluster_name"
  if CLUSTER_NAME="$cluster_name" docker-compose -f docker/docker-compose.yml --env-file "$env_file" -p "$cluster_name" up -d; then
    print_success "Docker Compose started successfully"
  else
    print_error "Failed to start cluster with docker-compose"
    exit 1
  fi

  # Wait for services to be healthy
  wait_for_health "$cluster_name"

  # Show cluster information
  show_cluster_info "$cluster_name"

  print_success "Cluster '$cluster_name' is ready!"
}

main "$@"
