#!/bin/bash

##############################################################################
# shell-cluster.sh
#
# Opens an interactive shell in a specific cluster service
#
# Usage: ./scripts/shell-cluster.sh <cluster-name> <service-name>
# Example: ./scripts/shell-cluster.sh dev fastapi
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
  echo -e "${BLUE}=== Shell Access ===${NC}\n"
}

show_usage() {
  cat << EOF
${BLUE}Usage: ./scripts/shell-cluster.sh <cluster-name> <service-name>${NC}

${YELLOW}Arguments:${NC}
  <cluster-name>   Name of the cluster (e.g., 'dev', 'agent-1')
  <service-name>   Name of the service to access (e.g., 'fastapi', 'postgres')

${YELLOW}Common services:${NC}
  - fastapi              (Python FastAPI application)
  - postgres             (PostgreSQL database)
  - postgrest            (PostgREST API)
  - litellm_proxy        (LiteLLM proxy service)
  - job_processor        (Background job processor)
  - landing_page         (Landing page service)

${YELLOW}Examples:${NC}
  ./scripts/shell-cluster.sh dev fastapi
  ./scripts/shell-cluster.sh agent-1 postgres
  ./scripts/shell-cluster.sh dev job_processor

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

is_cluster_running() {
  local cluster_name=$1

  CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps 2>/dev/null | grep -q " Up " || return 1
}

service_exists() {
  local cluster_name=$1
  local service_name=$2

  CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps 2>/dev/null | grep -q "^${cluster_name}-${service_name}" || return 1
}

get_container_id() {
  local cluster_name=$1
  local service_name=$2

  CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps -q "$service_name" 2>/dev/null || echo ""
}

##############################################################################
# Main
##############################################################################

main() {
  local cluster_name=$1
  local service_name=$2

  # Validate arguments
  if [ -z "$cluster_name" ] || [ -z "$service_name" ]; then
    print_error "Both cluster name and service name are required"
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

  # Check if cluster is running
  if ! is_cluster_running "$cluster_name"; then
    print_error "Cluster '$cluster_name' is not running"
    echo ""
    print_info "Start the cluster with: ./scripts/start-cluster.sh $cluster_name"
    exit 1
  fi

  # Check if service exists
  if ! service_exists "$cluster_name" "$service_name"; then
    print_error "Service '$service_name' not found in cluster '$cluster_name'"
    echo ""
    print_info "Available services in cluster '$cluster_name':"
    CLUSTER_NAME="$cluster_name" docker-compose --env-file "$env_file" -p "$cluster_name" ps --services | sed 's/^/  - /'
    exit 1
  fi

  print_info "Entering shell for service: $service_name"
  echo -e "${YELLOW}Type 'exit' to leave${NC}\n"

  cd "$PROJECT_ROOT"

  # Try to execute bash, fall back to sh if not available
  if CLUSTER_NAME="$cluster_name" docker-compose --env-file "$env_file" -p "$cluster_name" exec "$service_name" bash 2>/dev/null; then
    :
  elif CLUSTER_NAME="$cluster_name" docker-compose --env-file "$env_file" -p "$cluster_name" exec "$service_name" sh 2>/dev/null; then
    :
  else
    print_error "Failed to open shell in service '$service_name'"
    exit 1
  fi
}

main "$@"
