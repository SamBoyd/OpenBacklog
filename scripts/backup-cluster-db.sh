#!/bin/bash

##############################################################################
# backup-cluster-db.sh
#
# Creates a PostgreSQL backup for a specific cluster using pg_dump.
# Runs hourly via cron, but no-ops if a backup already exists for today.
# Retains backups for 7 days, automatically deleting older ones.
#
# Usage: ./scripts/backup-cluster-db.sh <cluster-name>
# Example: ./scripts/backup-cluster-db.sh longliving
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
BACKUP_DIR="$PROJECT_ROOT/backups"
RETENTION_DAYS=7

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
  echo -e "${BLUE}=== Database Backup ===${NC}\n"
}

show_usage() {
  echo -e "${BLUE}Usage: ./scripts/backup-cluster-db.sh <cluster-name>${NC}"
  echo ""
  echo -e "${YELLOW}Arguments:${NC}"
  echo "  <cluster-name>  Name of the cluster to backup (e.g., 'longliving', 'dev')"
  echo ""
  echo -e "${YELLOW}Examples:${NC}"
  echo "  ./scripts/backup-cluster-db.sh longliving"
  echo "  ./scripts/backup-cluster-db.sh dev"
  echo ""
  echo -e "${YELLOW}Notes:${NC}"
  echo "  - Backups are stored in ./backups/ directory"
  echo "  - Only one backup per day is created (subsequent runs skip)"
  echo "  - Backups older than ${RETENTION_DAYS} days are automatically deleted"
}

check_docker() {
  if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
  fi
}

find_env_file() {
  local cluster_name=$1

  # Try .env.{cluster} first (e.g., .env.longliving)
  if [ -f "$PROJECT_ROOT/.env.$cluster_name" ]; then
    echo "$PROJECT_ROOT/.env.$cluster_name"
    return 0
  fi

  # Try .env.cluster-{cluster} (e.g., .env.cluster-dev)
  if [ -f "$PROJECT_ROOT/.env.cluster-$cluster_name" ]; then
    echo "$PROJECT_ROOT/.env.cluster-$cluster_name"
    return 0
  fi

  return 1
}

get_value_from_env() {
  local env_file=$1
  local var_name=$2

  if [ -f "$env_file" ]; then
    grep "^${var_name}=" "$env_file" | cut -d'=' -f2 | tr -d ' ' || echo ""
  fi
}

check_container_running() {
  local cluster_name=$1
  local container_name="${cluster_name}-postgres-1"

  if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
    print_error "Container '$container_name' is not running"
    print_info "Start the cluster first: ./scripts/start-cluster.sh $cluster_name"
    exit 1
  fi
}

backup_exists_today() {
  local cluster_name=$1
  local today=$(date +%Y-%m-%d)

  if ls "$BACKUP_DIR/${cluster_name}_${today}"_*.sql.gz 1>/dev/null 2>&1; then
    return 0
  fi
  return 1
}

cleanup_old_backups() {
  local cluster_name=$1
  local deleted_count=0

  if [ -d "$BACKUP_DIR" ]; then
    deleted_count=$(find "$BACKUP_DIR" -name "${cluster_name}_*.sql.gz" -mtime +${RETENTION_DAYS} -type f -print -delete 2>/dev/null | wc -l | tr -d ' ')
  fi

  if [ "$deleted_count" -gt 0 ]; then
    print_info "Cleaned up $deleted_count old backup(s)"
  fi
}

count_backups() {
  local cluster_name=$1

  if [ -d "$BACKUP_DIR" ]; then
    find "$BACKUP_DIR" -name "${cluster_name}_*.sql.gz" -type f 2>/dev/null | wc -l | tr -d ' '
  else
    echo "0"
  fi
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

  # Find environment file
  local env_file
  if ! env_file=$(find_env_file "$cluster_name"); then
    print_error "No environment file found for cluster '$cluster_name'"
    print_info "Expected: .env.$cluster_name or .env.cluster-$cluster_name"
    exit 1
  fi

  print_info "Cluster: $cluster_name"
  print_info "Environment: $env_file"

  # Check if container is running
  check_container_running "$cluster_name"

  # Create backup directory
  mkdir -p "$BACKUP_DIR"

  # Check if backup already exists for today
  if backup_exists_today "$cluster_name"; then
    local existing=$(ls -1 "$BACKUP_DIR/${cluster_name}_$(date +%Y-%m-%d)"_*.sql.gz 2>/dev/null | head -1)
    print_warning "Backup already exists for today: $(basename "$existing")"
    print_info "Skipping backup"
    exit 0
  fi

  # Get database credentials from env file
  local postgres_user=$(get_value_from_env "$env_file" "POSTGRES_USER")
  local postgres_db=$(get_value_from_env "$env_file" "POSTGRES_DB")

  if [ -z "$postgres_user" ] || [ -z "$postgres_db" ]; then
    print_error "Could not find POSTGRES_USER or POSTGRES_DB in $env_file"
    exit 1
  fi

  # Generate backup filename
  local timestamp=$(date +%Y-%m-%d_%H%M%S)
  local backup_file="${cluster_name}_${timestamp}.sql.gz"
  local backup_path="$BACKUP_DIR/$backup_file"

  print_info "Creating backup: $backup_file"

  # Run pg_dump
  local container_name="${cluster_name}-postgres-1"
  if docker exec "$container_name" pg_dump -U "$postgres_user" "$postgres_db" | gzip > "$backup_path"; then
    local backup_size=$(ls -lh "$backup_path" | awk '{print $5}')
    print_success "Backup created: $backup_file ($backup_size)"
  else
    print_error "Failed to create backup"
    rm -f "$backup_path"
    exit 1
  fi

  # Cleanup old backups
  cleanup_old_backups "$cluster_name"

  # Show summary
  local total_backups=$(count_backups "$cluster_name")
  echo ""
  print_success "Backup complete! ($total_backups backup(s) retained)"
}

main "$@"
