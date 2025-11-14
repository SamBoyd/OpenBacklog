#!/bin/bash

##############################################################################
# rebuild-cluster.sh
#
# Rebuilds Docker images for a specific cluster and optionally restarts it.
# Supports rebuilding all services or a specific service.
#
# Usage: ./scripts/rebuild-cluster.sh <cluster-name> [service-name] [--no-cache]
# Example: ./scripts/rebuild-cluster.sh dev
#          ./scripts/rebuild-cluster.sh dev fastapi
#          ./scripts/rebuild-cluster.sh agent-1 --no-cache
#          ./scripts/rebuild-cluster.sh dev fastapi --no-cache
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

# Buildable services
BUILDABLE_SERVICES=("fastapi" "litellm_proxy" "job_processor" "unified_background_worker")

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

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_header() {
  echo -e "${BLUE}=== Rebuilding Cluster ===${NC}\\n"
}

show_usage() {
  cat << EOF
${BLUE}Usage: ./scripts/rebuild-cluster.sh <cluster-name> [service-name] [--no-cache]${NC}

${YELLOW}Arguments:${NC}
  <cluster-name>  Required. Name of the cluster (e.g., 'dev', 'agent-1')
  [service-name]  Optional. Specific service to rebuild. If omitted, rebuilds all.
                  Valid services: ${BUILDABLE_SERVICES[*]}
  --no-cache      Optional. Force complete rebuild without Docker cache

${YELLOW}Examples:${NC}
  ./scripts/rebuild-cluster.sh dev                    # Rebuild all services
  ./scripts/rebuild-cluster.sh dev fastapi            # Rebuild only fastapi
  ./scripts/rebuild-cluster.sh agent-1 --no-cache     # Rebuild all, no cache
  ./scripts/rebuild-cluster.sh dev fastapi --no-cache # Rebuild fastapi, no cache

${YELLOW}Available clusters:${NC}
EOF
  find "$PROJECT_ROOT" -maxdepth 1 -name ".env.cluster-*" -type f -printf '%f\n' 2>/dev/null | \
    sed 's/^\\.env\\.cluster-/  - /' || echo "  (none configured)"
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

is_valid_service() {
  local service=$1
  for valid_service in "${BUILDABLE_SERVICES[@]}"; do
    if [ "$service" = "$valid_service" ]; then
      return 0
    fi
  done
  return 1
}

is_cluster_running() {
  local cluster_name=$1

  # Try to check if cluster has any running services
  CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps 2>/dev/null | grep -q " Up " || return 1
}

get_value_from_env() {
  local env_file=$1
  local var_name=$2

  if [ -f "$env_file" ]; then
    grep "^${var_name}=" "$env_file" | cut -d'=' -f2 | tr -d ' ' || echo ""
  fi
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
  local cluster_name=""
  local service_name=""
  local no_cache=false

  # Parse arguments
  if [ -z "$1" ]; then
    print_error "Cluster name is required"
    echo ""
    show_usage
    exit 1
  fi

  if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
  fi

  cluster_name=$1
  shift || true

  # Parse remaining arguments (service name and/or --no-cache flag)
  while [ $# -gt 0 ]; do
    case "$1" in
      --no-cache)
        no_cache=true
        shift
        ;;
      *)
        # Assume it's a service name
        if is_valid_service "$1"; then
          service_name=$1
          shift
        else
          print_error "Invalid service name: $1"
          echo "Valid services: ${BUILDABLE_SERVICES[*]}"
          exit 1
        fi
        ;;
    esac
  done

  print_header

  # Pre-flight checks
  check_docker
  validate_cluster "$cluster_name"

  local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

  # Display build information
  print_info "Cluster name: $cluster_name"
  if [ -n "$service_name" ]; then
    print_info "Service to rebuild: $service_name"
  else
    print_info "Services to rebuild: ALL (${BUILDABLE_SERVICES[*]})"
  fi
  if [ "$no_cache" = true ]; then
    print_warning "Docker cache will be SKIPPED"
  else
    print_info "Docker cache: will be used (faster rebuilds)"
  fi
  echo ""

  # Check if cluster is running
  if is_cluster_running "$cluster_name"; then
    print_info "Stopping cluster '$cluster_name'..."
    cd "$PROJECT_ROOT"
    if CLUSTER_NAME="$cluster_name" docker-compose -f docker/docker-compose.yml --env-file "$env_file" -p "$cluster_name" down; then
      print_success "Cluster stopped"
    else
      print_error "Failed to stop cluster"
      exit 1
    fi
  else
    print_warning "Cluster '$cluster_name' is not currently running"
  fi

  echo ""

  # Build the Docker images
  print_info "Building Docker images for cluster: $cluster_name..."
  cd "$PROJECT_ROOT"

  local build_args=""
  if [ "$no_cache" = true ]; then
    build_args="--no-cache"
  fi

  if [ -n "$service_name" ]; then
    # Build specific service
    print_info "Building service: $service_name..."
    if CLUSTER_NAME="$cluster_name" docker-compose -f docker/docker-compose.yml --env-file "$env_file" -p "$cluster_name" build $build_args "$service_name"; then
      print_success "Service '$service_name' built successfully"
    else
      print_error "Failed to build service '$service_name'"
      exit 1
    fi
  else
    # Build all buildable services
    for service in "${BUILDABLE_SERVICES[@]}"; do
      print_info "Building service: $service..."
      if CLUSTER_NAME="$cluster_name" docker-compose -f docker/docker-compose.yml --env-file "$env_file" -p "$cluster_name" build $build_args "$service"; then
        print_success "Service '$service' built successfully"
      else
        print_error "Failed to build service '$service'"
        exit 1
      fi
    done
  fi

  echo ""

  # Start the cluster
  print_info "Starting cluster..."
  if CLUSTER_NAME="$cluster_name" docker-compose -f docker/docker-compose.yml --env-file "$env_file" -p "$cluster_name" up -d; then
    print_success "Cluster started successfully"
  else
    print_error "Failed to start cluster"
    exit 1
  fi

  echo ""

  # Show cluster information
  show_cluster_info "$cluster_name"

  print_success "Cluster '$cluster_name' has been rebuilt and restarted!"
}

main "$@"
