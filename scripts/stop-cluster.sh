#!/bin/bash

##############################################################################
# stop-cluster.sh
#
# Stops a specific cluster safely with optional volume removal
#
# Usage: ./scripts/stop-cluster.sh <cluster-name> [--volumes]
# Example: ./scripts/stop-cluster.sh dev
#          ./scripts/stop-cluster.sh agent-1 --volumes
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

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_header() {
  echo -e "${BLUE}=== Stopping Cluster ===${NC}\n"
}

show_usage() {
  cat << EOF
${BLUE}Usage: ./scripts/stop-cluster.sh <cluster-name> [--volumes]${NC}

${YELLOW}Arguments:${NC}
  <cluster-name>  Name of the cluster to stop (e.g., 'dev', 'agent-1')
  --volumes       Optional flag to remove volumes (default: preserve volumes)

${YELLOW}Examples:${NC}
  ./scripts/stop-cluster.sh dev              # Stop, keep data
  ./scripts/stop-cluster.sh agent-1 --volumes # Stop, remove volumes

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

  # Try to check if cluster has any running services
  CLUSTER_NAME="$cluster_name" docker-compose --env-file ".env.cluster-${cluster_name}" -p "${cluster_name}" ps 2>/dev/null | grep -q " Up " || return 1
}

confirm_action() {
  local prompt=$1
  local response

  while true; do
    echo -n -e "${YELLOW}${prompt} (y/n): ${NC}"
    read -r -n 1 response
    echo ""

    case "$response" in
      [yY]) return 0 ;;
      [nN]) return 1 ;;
      *) echo -e "${RED}Please answer y or n${NC}" ;;
    esac
  done
}

##############################################################################
# Main
##############################################################################

main() {
  local cluster_name=$1
  local remove_volumes=false

  # Parse arguments
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

  # Check for --volumes flag
  if [ -n "$2" ] && [ "$2" = "--volumes" ]; then
    remove_volumes=true
  fi

  print_header

  # Pre-flight checks
  check_docker
  validate_cluster "$cluster_name"

  local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

  # Check if cluster is running
  if ! is_cluster_running "$cluster_name"; then
    print_warning "Cluster '$cluster_name' is not currently running"
    echo ""
    read -p "Continue with stop command anyway? (y/n): " -n 1 response
    echo ""
    if [[ ! "$response" =~ ^[yY]$ ]]; then
      print_info "Stop cancelled"
      exit 0
    fi
  fi

  print_info "Cluster name: $cluster_name"
  if [ "$remove_volumes" = true ]; then
    print_warning "Volumes will be REMOVED"
  else
    print_info "Volumes will be PRESERVED"
  fi
  echo ""

  # Confirm if removing volumes
  if [ "$remove_volumes" = true ]; then
    print_warning "All data in volumes will be permanently deleted!"
    if ! confirm_action "Are you sure you want to remove volumes?"; then
      print_info "Stop cancelled"
      exit 0
    fi
  fi

  # Stop the cluster
  echo ""
  print_info "Stopping cluster..."
  cd "$PROJECT_ROOT"

  local compose_args="--env-file $env_file -p $cluster_name"
  if [ "$remove_volumes" = true ]; then
    if CLUSTER_NAME="$cluster_name" docker-compose $compose_args down -v; then
      print_success "Cluster stopped and volumes removed"
    else
      print_error "Failed to stop cluster and remove volumes"
      exit 1
    fi
  else
    if CLUSTER_NAME="$cluster_name" docker-compose $compose_args down; then
      print_success "Cluster stopped (data preserved)"
    else
      print_error "Failed to stop cluster"
      exit 1
    fi
  fi

  print_success "Cluster '$cluster_name' has been stopped"

  if [ "$remove_volumes" = false ]; then
    echo ""
    print_info "To remove volumes later, run: ./scripts/stop-cluster.sh $cluster_name --volumes"
  fi
}

main "$@"
