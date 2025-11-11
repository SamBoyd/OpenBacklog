#!/bin/bash

##############################################################################
# logs-cluster.sh
#
# Tails logs for a cluster or specific service within a cluster
#
# Usage: ./scripts/logs-cluster.sh <cluster-name> [service-name] [options]
# Example: ./scripts/logs-cluster.sh dev
#          ./scripts/logs-cluster.sh dev fastapi
#          ./scripts/logs-cluster.sh agent-1 postgres -n 50
#
##############################################################################

# Note: We use 'set -e' only after handling --help to allow normal exit
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
  echo -e "${BLUE}=== Cluster Logs ===${NC}\n"
}

show_usage() {
  cat << EOF
${BLUE}Usage: ./scripts/logs-cluster.sh <cluster-name> [service-name] [options]${NC}

${YELLOW}Arguments:${NC}
  <cluster-name>   Name of the cluster (e.g., 'dev', 'agent-1')
  [service-name]   Optional service name (shows all services if omitted)
  [options]        Docker-compose logs options

${YELLOW}Common services:${NC}
  - fastapi              (Python FastAPI application)
  - postgres             (PostgreSQL database)
  - postgrest            (PostgREST API)
  - litellm_proxy        (LiteLLM proxy service)
  - job_processor        (Background job processor)
  - landing_page         (Landing page service)

${YELLOW}Docker options (passed through):${NC}
  -f, --follow          Follow log output (default)
  -n, --tail N          Show last N lines
  --timestamps          Show timestamps
  --no-colors           Disable colors

${YELLOW}Examples:${NC}
  ./scripts/logs-cluster.sh dev                   # All services, follow mode
  ./scripts/logs-cluster.sh dev fastapi           # FastAPI logs only
  ./scripts/logs-cluster.sh agent-1 postgres -n 100  # Last 100 lines
  ./scripts/logs-cluster.sh dev --tail 50         # All services, last 50 lines

${YELLOW}Exiting logs:${NC}
  Press Ctrl+C to exit (when following logs)

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

list_services() {
  local cluster_name=$1
  CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps --services 2>/dev/null || true
}

##############################################################################
# Main
##############################################################################

main() {
  local cluster_name=$1
  local service_name=""
  shift 2>/dev/null || true

  # Handle no arguments
  if [ -z "$cluster_name" ]; then
    print_error "Cluster name is required"
    echo ""
    show_usage
    exit 1
  fi

  # Handle help
  if [ "$cluster_name" = "--help" ] || [ "$cluster_name" = "-h" ]; then
    show_usage
    exit 0
  fi

  set -e

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

  # Check if service was specified and exists
  if [ -n "$1" ] && [ "${1:0:1}" != "-" ]; then
    service_name=$1
    shift 2>/dev/null || true

    if ! service_exists "$cluster_name" "$service_name"; then
      print_error "Service '$service_name' not found in cluster '$cluster_name'"
      echo ""
      print_info "Available services in cluster '$cluster_name':"
      list_services "$cluster_name" | sed 's/^/  - /'
      exit 1
    fi

    print_info "Showing logs for service: $service_name (Press Ctrl+C to exit)"
  else
    print_info "Showing logs for all services (Press Ctrl+C to exit)"
    # Shift back the argument that was already shifted in the main call
    # to preserve any docker options that were passed
  fi

  echo ""

  # Build docker-compose logs command
  cd "$PROJECT_ROOT"

  # Run docker-compose logs with service name (if provided) and any additional options
  set +e  # Don't exit on Ctrl+C
  if [ -n "$service_name" ]; then
    CLUSTER_NAME="$cluster_name" docker-compose --env-file "$env_file" -p "$cluster_name" logs -f "$service_name" "$@"
  else
    CLUSTER_NAME="$cluster_name" docker-compose --env-file "$env_file" -p "$cluster_name" logs -f "$@"
  fi
  local exit_code=$?
  set -e

  # Ctrl+C returns 130, which is normal for log following
  if [ $exit_code -eq 130 ]; then
    echo -e "\n${CYAN}Log stream closed${NC}"
    exit 0
  elif [ $exit_code -ne 0 ]; then
    exit $exit_code
  fi
}

main "$@"
