#!/bin/bash

# ============================================================================
# OpenBacklog Multi-Cluster Setup Script
# ============================================================================
# Usage:
#   ./scripts/setup-cluster.sh create dev       # Create primary dev cluster
#   ./scripts/setup-cluster.sh create agent-1   # Create agent cluster 1
#   ./scripts/setup-cluster.sh create agent-2   # Create agent cluster 2
#
# This script:
# 1. Validates cluster name format
# 2. Determines cluster type (primary vs agent)
# 3. Calculates port offsets based on cluster number
# 4. Generates .env.cluster-{name} from .env.template
# 5. Creates Docker network configuration
# 6. For primary cluster: Verifies /etc/hosts entries
# 7. Outputs configuration summary
# ============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$PROJECT_ROOT/.env.template"
HOSTS_FILE="/etc/hosts"

# ============================================================================
# Helper Functions
# ============================================================================

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

# ============================================================================
# Validation Functions
# ============================================================================

validate_template_exists() {
    if [ ! -f "$TEMPLATE_FILE" ]; then
        print_error "Template file not found: $TEMPLATE_FILE"
        print_info "Run this script from the project root directory"
        exit 1
    fi
}

validate_cluster_name() {
    local cluster_name="$1"

    # Valid cluster names: "dev" or "agent-N" where N is a number
    if [[ "$cluster_name" == "dev" ]]; then
        return 0
    elif [[ "$cluster_name" =~ ^agent-[0-9]+$ ]]; then
        return 0
    else
        print_error "Invalid cluster name: $cluster_name"
        echo "Valid formats: 'dev' or 'agent-N' (where N is a number)"
        echo "Examples: dev, agent-1, agent-2, agent-3"
        exit 1
    fi
}

# ============================================================================
# Cluster Configuration Functions
# ============================================================================

get_cluster_type() {
    local cluster_name="$1"
    if [ "$cluster_name" == "dev" ]; then
        echo "primary"
    else
        echo "agent"
    fi
}

get_cluster_number() {
    local cluster_name="$1"
    if [ "$cluster_name" == "dev" ]; then
        echo "0"
    else
        # Extract number from "agent-N" format
        echo "${cluster_name#agent-}"
    fi
}

calculate_ports() {
    local cluster_number="$1"

    # Port calculation:
    # Primary (0):  Nginx=80, FastAPI=8000, PostgREST=3000, Postgres=5433, Memory=5434, LiteLLM_DB=5435, LiteLLM=4000, Landing=7777
    # Agent-1 (1):  Nginx=81, FastAPI=8001, PostgREST=3001, Postgres=5436, Memory=5437, LiteLLM_DB=5438, LiteLLM=4001, Landing=7778
    # Agent-2 (2):  Nginx=82, FastAPI=8002, PostgREST=3002, Postgres=5439, Memory=5440, LiteLLM_DB=5441, LiteLLM=4002, Landing=7779

    local nginx_port=$((80 + cluster_number))
    local fastapi_port=$((8000 + cluster_number))
    local postgrest_port=$((3000 + cluster_number))
    local postgres_port=$((5433 + cluster_number * 3))
    local postgres_memory_port=$((5434 + cluster_number * 3))
    local postgres_litellm_port=$((5435 + cluster_number * 3))
    local litellm_port=$((4000 + cluster_number))
    local landing_page_port=$((7777 + cluster_number))

    echo "$nginx_port $fastapi_port $postgrest_port $postgres_port $postgres_memory_port $postgres_litellm_port $litellm_port $landing_page_port"
}

# ============================================================================
# Environment File Generation
# ============================================================================

generate_cluster_env() {
    local cluster_name="$1"
    local cluster_type="$2"
    local cluster_number="$3"
    local output_file="$4"

    # Read ports
    read -r nginx_port fastapi_port postgrest_port postgres_port postgres_memory_port postgres_litellm_port litellm_port landing_page_port <<< "$(calculate_ports "$cluster_number")"

    # Determine app_domain and related settings
    local docker_network_name="${cluster_name}-net"

    if [ "$cluster_type" == "primary" ]; then
        app_domain="dev.openbacklog.ai"
        app_url="http://dev.openbacklog.ai"
        static_site_url="http://www.dev.openbacklog.ai"
        static_site_domain="www.dev.openbacklog.ai"
    else
        # Note: app_domain and static_site_domain are used in nginx server_name directives
        # and must NOT include ports. Nginx matches on hostname only; the port is matched
        # via the listen directive and docker port mapping.
        app_domain="agent-$cluster_number.openbacklog.ai"
        app_url="http://agent-$cluster_number.openbacklog.ai:$nginx_port"
        static_site_url="http://www.agent-$cluster_number.openbacklog.ai:$nginx_port"
        static_site_domain="www.agent-$cluster_number.openbacklog.ai"
    fi

    # Copy template and replace cluster-specific variables
    cp "$TEMPLATE_FILE" "$output_file"

    # Replace cluster-specific port variables
    sed -i.bak "s/^NGINX_PORT=.*/NGINX_PORT=$nginx_port/" "$output_file"
    sed -i.bak "s/^FASTAPI_PORT=.*/FASTAPI_PORT=$fastapi_port/" "$output_file"
    sed -i.bak "s/^POSTGREST_PORT=.*/POSTGREST_PORT=$postgrest_port/" "$output_file"
    sed -i.bak "s/^POSTGRES_PORT=.*/POSTGRES_PORT=$postgres_port/" "$output_file"
    sed -i.bak "s/^POSTGRES_MEMORY_PORT=.*/POSTGRES_MEMORY_PORT=$postgres_memory_port/" "$output_file"
    sed -i.bak "s/^POSTGRES_LITELLM_PORT=.*/POSTGRES_LITELLM_PORT=$postgres_litellm_port/" "$output_file"
    sed -i.bak "s/^LITELLM_PORT=.*/LITELLM_PORT=$litellm_port/" "$output_file"
    sed -i.bak "s/^LANDING_PAGE_PORT=.*/LANDING_PAGE_PORT=$landing_page_port/" "$output_file"

    # Replace Docker network name
    sed -i.bak "s/^DOCKER_NETWORK_NAME=.*/DOCKER_NETWORK_NAME=$docker_network_name/" "$output_file"

    # Replace app domain settings
    sed -i.bak "s|^app_domain=.*|app_domain=$app_domain|" "$output_file"
    sed -i.bak "s|^app_url=.*|app_url=$app_url|" "$output_file"
    sed -i.bak "s|^static_site_url=.*|static_site_url=$static_site_url|" "$output_file"
    sed -i.bak "s|^static_site_domain=.*|static_site_domain=$static_site_domain|" "$output_file"

    # Remove backup files
    rm -f "$output_file.bak"
}

# ============================================================================
# /etc/hosts Verification
# ============================================================================

check_hosts_entries() {
    local cluster_name="$1"

    if [ "$cluster_name" != "dev" ]; then
        # Agent clusters don't need /etc/hosts entries
        return 0
    fi

    print_header "Verifying /etc/hosts entries"

    local needs_update=false
    local entries=(
        "127.0.0.1  dev.openbacklog.ai"
        "127.0.0.1  www.dev.openbacklog.ai"
    )

    for entry in "${entries[@]}"; do
        if grep -q "^$entry" "$HOSTS_FILE" 2>/dev/null; then
            print_success "Found: $entry"
        else
            print_warning "Missing: $entry"
            needs_update=true
        fi
    done

    if [ "$needs_update" = true ]; then
        print_info ""
        print_info "To add missing entries, run:"
        echo ""
        echo "  sudo tee -a $HOSTS_FILE > /dev/null <<EOF"
        for entry in "${entries[@]}"; do
            if ! grep -q "^$entry" "$HOSTS_FILE" 2>/dev/null; then
                echo "$entry"
            fi
        done
        echo "EOF"
        echo ""
        print_info "Then verify with: cat /etc/hosts | grep dev.openbacklog.ai"
    fi
}

# ============================================================================
# Cluster Configuration Summary
# ============================================================================

print_cluster_summary() {
    local cluster_name="$1"
    local cluster_type="$2"
    local cluster_number="$3"

    read -r nginx_port fastapi_port postgrest_port postgres_port postgres_memory_port postgres_litellm_port litellm_port landing_page_port <<< "$(calculate_ports "$cluster_number")"

    print_header "Cluster Configuration Summary"

    echo -e "Cluster Name:     ${YELLOW}$cluster_name${NC}"
    echo -e "Cluster Type:     ${YELLOW}$cluster_type${NC}"
    echo -e "Docker Network:   ${YELLOW}${cluster_name}-net${NC}"
    echo ""

    if [ "$cluster_type" == "primary" ]; then
        echo -e "Access URLs (Primary Cluster - Port 80, no port needed in URL):"
        echo -e "  FastAPI API:      ${GREEN}http://dev.openbacklog.ai${NC}"
        echo -e "  Landing Page:     ${GREEN}http://www.dev.openbacklog.ai${NC}"
        echo -e "  PostgREST (int):  ${GREEN}http://localhost:$postgrest_port${NC}"
    else
        echo -e "Access URLs (Agent Cluster - Port required in URL):"
        echo -e "  FastAPI API:      ${GREEN}http://localhost:$fastapi_port${NC}"
        echo -e "  Landing Page:     ${GREEN}http://localhost:$landing_page_port${NC}"
        echo -e "  PostgREST (int):  ${GREEN}http://localhost:$postgrest_port${NC}"
    fi

    echo ""
    echo -e "Port Mappings (External):"
    echo -e "  Nginx:            ${BLUE}$nginx_port${NC}"
    echo -e "  FastAPI:          ${BLUE}$fastapi_port${NC}"
    echo -e "  PostgREST:        ${BLUE}$postgrest_port${NC}"
    echo -e "  PostgreSQL:       ${BLUE}$postgres_port${NC}"
    echo -e "  PostgreSQL Memory: ${BLUE}$postgres_memory_port${NC}"
    echo -e "  PostgreSQL LiteLLM: ${BLUE}$postgres_litellm_port${NC}"
    echo -e "  LiteLLM Proxy:    ${BLUE}$litellm_port${NC}"
    echo -e "  Landing Page:     ${BLUE}$landing_page_port${NC}"
    echo ""

    echo -e "Database Names:"
    echo -e "  Main:             ${BLUE}${cluster_name}-db${NC}"
    echo -e "  Memory:           ${BLUE}${cluster_name}-memory_db${NC}"
    echo -e "  LiteLLM:          ${BLUE}${cluster_name}-litellm_db${NC}"
    echo ""

    echo -e "Configuration File: ${GREEN}$PROJECT_ROOT/.env.cluster-$cluster_name${NC}"
    echo ""
}

# ============================================================================
# Port Availability Check
# ============================================================================

check_port_available() {
    local port="$1"
    local port_name="$2"

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port ($port_name) is already in use"
        return 1
    fi
    return 0
}

verify_ports_available() {
    local cluster_number="$1"

    read -r nginx_port fastapi_port postgrest_port postgres_port postgres_memory_port postgres_litellm_port litellm_port landing_page_port <<< "$(calculate_ports "$cluster_number")"

    print_header "Checking Port Availability"

    local ports_ok=true
    check_port_available "$nginx_port" "Nginx" || ports_ok=false
    check_port_available "$fastapi_port" "FastAPI" || ports_ok=false
    check_port_available "$postgrest_port" "PostgREST" || ports_ok=false
    check_port_available "$postgres_port" "PostgreSQL" || ports_ok=false
    check_port_available "$postgres_memory_port" "PostgreSQL Memory" || ports_ok=false
    check_port_available "$postgres_litellm_port" "PostgreSQL LiteLLM" || ports_ok=false
    check_port_available "$litellm_port" "LiteLLM" || ports_ok=false
    check_port_available "$landing_page_port" "Landing Page" || ports_ok=false

    if [ "$ports_ok" = true ]; then
        print_success "All ports are available"
    else
        print_error "Some ports are already in use. Please stop conflicting containers."
        exit 1
    fi
}

# ============================================================================
# Cluster Environment File Existence Check
# ============================================================================

check_env_exists() {
    local cluster_name="$1"
    local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

    if [ -f "$env_file" ]; then
        print_warning "Environment file already exists: $env_file"
        read -p "Overwrite? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cancelled cluster creation"
            exit 0
        fi
    fi
}

# ============================================================================
# Main Setup Flow
# ============================================================================

main() {
    local action="${1:-}"
    local cluster_name="${2:-}"

    # Validate arguments
    if [ -z "$action" ] || [ -z "$cluster_name" ]; then
        echo "OpenBacklog Multi-Cluster Setup"
        echo ""
        echo "Usage: ./scripts/setup-cluster.sh create <cluster-name>"
        echo ""
        echo "Examples:"
        echo "  ./scripts/setup-cluster.sh create dev       # Primary development cluster"
        echo "  ./scripts/setup-cluster.sh create agent-1   # Agent cluster 1"
        echo "  ./scripts/setup-cluster.sh create agent-2   # Agent cluster 2"
        echo "  ./scripts/setup-cluster.sh create agent-3   # Agent cluster 3"
        exit 1
    fi

    if [ "$action" != "create" ]; then
        print_error "Unknown action: $action"
        echo "Use 'create' to setup a new cluster"
        exit 1
    fi

    # Validate template and cluster name
    validate_template_exists
    validate_cluster_name "$cluster_name"

    # Determine cluster properties
    local cluster_type=$(get_cluster_type "$cluster_name")
    local cluster_number=$(get_cluster_number "$cluster_name")
    local env_file="$PROJECT_ROOT/.env.cluster-$cluster_name"

    print_header "Creating OpenBacklog Cluster"
    print_info "Cluster: $cluster_name (Type: $cluster_type)"

    # Verify environment file doesn't already exist
    check_env_exists "$cluster_name"

    # Check port availability
    verify_ports_available "$cluster_number"

    # Generate environment file
    print_header "Generating Environment Configuration"
    generate_cluster_env "$cluster_name" "$cluster_type" "$cluster_number" "$env_file"
    print_success "Created: $env_file"

    # Check /etc/hosts for primary cluster
    check_hosts_entries "$cluster_name"

    # Print summary
    print_cluster_summary "$cluster_name" "$cluster_type" "$cluster_number"

    print_success "Cluster setup complete!"
    echo ""
    echo -e "Next steps:"
    echo "  1. Start the cluster:"
    echo -e "     ${YELLOW}docker-compose --env-file .env.cluster-$cluster_name -p $cluster_name up -d${NC}"
    echo ""
    echo "  2. Verify it's running:"
    echo -e "     ${YELLOW}docker-compose --env-file .env.cluster-$cluster_name -p $cluster_name ps${NC}"
    echo ""
    echo "  3. Check logs:"
    echo -e "     ${YELLOW}docker-compose --env-file .env.cluster-$cluster_name -p $cluster_name logs -f fastapi${NC}"
    echo ""
}

main "$@"
