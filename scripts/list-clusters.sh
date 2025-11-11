#!/bin/bash

##############################################################################
# list-clusters.sh
#
# Lists all configured clusters and their current status
#
# Usage: ./scripts/list-clusters.sh
#
##############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

##############################################################################
# Functions
##############################################################################

print_header() {
  echo -e "${BLUE}=== OpenBacklog Cluster Status ===${NC}\n"
}

print_error() {
  echo -e "${RED}Error: $1${NC}" >&2
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

check_docker() {
  if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
  fi
}

# Extract port from .env file
get_port_from_env() {
  local env_file=$1
  local port_var=$2

  if [ -f "$env_file" ]; then
    grep "^${port_var}=" "$env_file" | cut -d'=' -f2 | tr -d ' '
  fi
}

# Extract value from .env file
get_value_from_env() {
  local env_file=$1
  local var_name=$2

  if [ -f "$env_file" ]; then
    grep "^${var_name}=" "$env_file" | cut -d'=' -f2 | tr -d ' '
  fi
}

# Check if cluster is running
is_cluster_running() {
  local cluster_name=$1

  if CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps --services > /dev/null 2>&1; then
    # Check if any services are running
    local running=$(CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps 2>/dev/null | grep -c " Up " || true)
    [ "$running" -gt 0 ]
  else
    return 1
  fi
}

list_clusters() {
  local found_clusters=0

  # Find all .env.cluster-* files
  local cluster_files=$(find "$PROJECT_ROOT" -maxdepth 1 -name ".env.cluster-*" -type f 2>/dev/null | sort)

  if [ -z "$cluster_files" ]; then
    print_warning "No clusters configured. Run './scripts/setup-cluster.sh create <cluster-name>' to create one."
    return 0
  fi

  # Print table header
  printf "%-15s %-12s %-25s %-12s %-10s %-20s\n" "CLUSTER" "STATUS" "FASTAPI URL" "POSTGREST" "DATABASE" "NETWORK"
  printf "%-15s %-12s %-25s %-12s %-10s %-20s\n" "-------" "------" "-----------" "----------" "--------" "-------"

  # Process each cluster file
  for cluster_file in $cluster_files; do
    local cluster_name=$(basename "$cluster_file" | sed 's/^\.env\.cluster-//')
    local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

    # Get ports and configuration from .env file
    local fastapi_port=$(get_port_from_env "$env_file" "FASTAPI_PORT")
    local postgrest_port=$(get_port_from_env "$env_file" "POSTGREST_PORT")
    local postgres_port=$(get_port_from_env "$env_file" "POSTGRES_PORT")
    local docker_network=$(get_value_from_env "$env_file" "DOCKER_NETWORK_NAME")

    # Default values if not found
    fastapi_port=${fastapi_port:-"N/A"}
    postgrest_port=${postgrest_port:-"N/A"}
    postgres_port=${postgres_port:-"N/A"}
    docker_network=${docker_network:-"${cluster_name}-net"}

    # Check if cluster is running
    local status_text="STOPPED"
    local status_color="${RED}"

    if is_cluster_running "$cluster_name"; then
      status_text="RUNNING"
      status_color="${GREEN}"
    fi

    # Construct FastAPI URL
    local fastapi_url="localhost:$fastapi_port"
    if [ "$fastapi_port" != "N/A" ]; then
      fastapi_url="${status_color}${fastapi_url}${NC}"
    fi

    # Print cluster row
    printf "%-15s ${status_color}%-12s${NC} %-25s %-12s %-10s %-20s\n" \
      "$cluster_name" \
      "$status_text" \
      "localhost:$fastapi_port" \
      "localhost:$postgrest_port" \
      "localhost:$postgres_port" \
      "$docker_network"

    ((found_clusters++))
  done

  if [ $found_clusters -eq 0 ]; then
    print_warning "No cluster configurations found."
    return 1
  fi

  echo ""
  print_success "Found $found_clusters cluster(s)"
}

##############################################################################
# Main
##############################################################################

main() {
  check_docker
  print_header
  list_clusters
}

main "$@"
