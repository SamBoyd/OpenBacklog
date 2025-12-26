#!/bin/bash

##############################################################################
# restore-cluster-db.sh
#
# Restores a PostgreSQL backup for a specific cluster.
# Lists available backups if no backup file is specified.
# Requires confirmation before restoring (use --yes to skip).
#
# Usage: ./scripts/restore-cluster-db.sh <cluster-name> [backup-file] [--yes]
# Example: ./scripts/restore-cluster-db.sh longliving
# Example: ./scripts/restore-cluster-db.sh longliving longliving_2024-01-15_120000.sql.gz
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
  echo -e "${BLUE}=== Database Restore ===${NC}\n"
}

show_usage() {
  echo -e "${BLUE}Usage: ./scripts/restore-cluster-db.sh <cluster-name> [backup-file] [--yes]${NC}"
  echo ""
  echo -e "${YELLOW}Arguments:${NC}"
  echo "  <cluster-name>  Name of the cluster to restore (e.g., 'longliving', 'dev')"
  echo "  [backup-file]   Optional: specific backup file to restore"
  echo "  [--yes]         Skip confirmation prompt"
  echo ""
  echo -e "${YELLOW}Examples:${NC}"
  echo "  ./scripts/restore-cluster-db.sh longliving"
  echo "    - Lists all available backups for the longliving cluster"
  echo ""
  echo "  ./scripts/restore-cluster-db.sh longliving longliving_2024-01-15_120000.sql.gz"
  echo "    - Restores the specified backup (with confirmation)"
  echo ""
  echo "  ./scripts/restore-cluster-db.sh longliving longliving_2024-01-15_120000.sql.gz --yes"
  echo "    - Restores without confirmation prompt"
  echo ""
  echo -e "${YELLOW}Notes:${NC}"
  echo "  - Backups are stored in ./backups/ directory"
  echo "  - Restore will DROP and recreate the database"
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

list_backups() {
  local cluster_name=$1

  if [ ! -d "$BACKUP_DIR" ]; then
    print_warning "No backups directory found"
    return 1
  fi

  local backups=$(find "$BACKUP_DIR" -name "${cluster_name}_*.sql.gz" -type f 2>/dev/null | sort -r)

  if [ -z "$backups" ]; then
    print_warning "No backups found for cluster '$cluster_name'"
    return 1
  fi

  echo -e "${BLUE}Available backups for '$cluster_name':${NC}\n"
  echo "$backups" | while read -r backup; do
    local filename=$(basename "$backup")
    local size=$(ls -lh "$backup" | awk '{print $5}')
    local date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup" 2>/dev/null || stat -c "%y" "$backup" 2>/dev/null | cut -d'.' -f1)
    echo -e "  ${CYAN}$filename${NC} ($size) - $date"
  done
  echo ""
  print_info "To restore: ./scripts/restore-cluster-db.sh $cluster_name <backup-file>"
}

confirm_restore() {
  local backup_file=$1
  local cluster_name=$2

  echo ""
  print_warning "This will DROP and recreate the database for cluster '$cluster_name'"
  print_warning "All current data will be replaced with the backup contents"
  echo ""
  read -p "Are you sure you want to restore from '$backup_file'? [y/N] " -n 1 -r
  echo ""

  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Restore cancelled"
    exit 0
  fi
}

##############################################################################
# Main
##############################################################################

main() {
  local cluster_name=$1
  local backup_file=$2
  local skip_confirm=false

  # Check for --yes flag
  for arg in "$@"; do
    if [ "$arg" = "--yes" ] || [ "$arg" = "-y" ]; then
      skip_confirm=true
    fi
  done

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

  # If no backup file specified, list available backups
  if [ -z "$backup_file" ] || [ "$backup_file" = "--yes" ] || [ "$backup_file" = "-y" ]; then
    list_backups "$cluster_name"
    exit 0
  fi

  print_info "Cluster: $cluster_name"
  print_info "Environment: $env_file"

  # Check if container is running
  check_container_running "$cluster_name"

  # Resolve backup file path
  local backup_path="$backup_file"
  if [ ! -f "$backup_path" ]; then
    backup_path="$BACKUP_DIR/$backup_file"
  fi

  if [ ! -f "$backup_path" ]; then
    print_error "Backup file not found: $backup_file"
    print_info "Check available backups: ./scripts/restore-cluster-db.sh $cluster_name"
    exit 1
  fi

  # Get database credentials from env file
  local postgres_user=$(get_value_from_env "$env_file" "POSTGRES_USER")
  local postgres_db=$(get_value_from_env "$env_file" "POSTGRES_DB")

  if [ -z "$postgres_user" ] || [ -z "$postgres_db" ]; then
    print_error "Could not find POSTGRES_USER or POSTGRES_DB in $env_file"
    exit 1
  fi

  # Confirm restore
  if [ "$skip_confirm" = false ]; then
    confirm_restore "$(basename "$backup_path")" "$cluster_name"
  fi

  print_info "Restoring from: $(basename "$backup_path")"

  local container_name="${cluster_name}-postgres-1"

  # Drop and recreate database
  print_info "Dropping existing database..."
  docker exec "$container_name" psql -U "$postgres_user" -d postgres -c "DROP DATABASE IF EXISTS $postgres_db;" 2>/dev/null || true

  print_info "Creating fresh database..."
  docker exec "$container_name" psql -U "$postgres_user" -d postgres -c "CREATE DATABASE $postgres_db OWNER $postgres_user;"

  # Restore from backup
  print_info "Restoring data..."
  if gunzip -c "$backup_path" | docker exec -i "$container_name" psql -U "$postgres_user" -d "$postgres_db" > /dev/null 2>&1; then
    echo ""
    print_success "Database restored successfully!"
    print_info "You may need to restart application services to pick up the changes"
  else
    print_error "Failed to restore database"
    exit 1
  fi
}

main "$@"
