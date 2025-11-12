#!/bin/bash

# Setup /etc/hosts entries for OpenBacklog clusters
# Usage: sudo ./scripts/setup-hosts.sh <cluster-name>
# Examples:
#   sudo ./scripts/setup-hosts.sh dev           # Add dev cluster hosts
#   sudo ./scripts/setup-hosts.sh agent-1       # Add agent-1 cluster hosts
#   sudo ./scripts/setup-hosts.sh all           # Add all cluster hosts

set -e

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo $0 <cluster-name>"
    exit 1
fi

CLUSTER_NAME="${1:-dev}"
HOSTS_FILE="/etc/hosts"
LOCALHOST="127.0.0.1"

# Define clusters - using simple case statement for POSIX compatibility
get_cluster_domains() {
    case "$1" in
        dev)
            echo "dev.openbacklog.ai www.dev.openbacklog.ai"
            ;;
        agent-1)
            echo "agent-1.openbacklog.ai www.agent-1.openbacklog.ai"
            ;;
        agent-2)
            echo "agent-2.openbacklog.ai www.agent-2.openbacklog.ai"
            ;;
        agent-3)
            echo "agent-3.openbacklog.ai www.agent-3.openbacklog.ai"
            ;;
        *)
            return 1
            ;;
    esac
}

# Get list of all clusters
get_all_clusters() {
    echo "dev agent-1 agent-2 agent-3"
}

# Function to add hosts entry
add_host_entry() {
    local ip=$1
    local hostname=$2
    local hosts_file=$3

    # Check if entry already exists
    if grep -q "^$ip[[:space:]]*$hostname" "$hosts_file"; then
        echo "✓ Already exists: $ip $hostname"
        return 0
    fi

    # Add the entry
    echo "$ip $hostname" >> "$hosts_file"
    echo "✓ Added: $ip $hostname"
}

# Function to setup a cluster
setup_cluster() {
    local cluster=$1
    local hostnames

    hostnames=$(get_cluster_domains "$cluster")
    if [ $? -ne 0 ]; then
        echo "Error: Unknown cluster '$cluster'"
        echo "Available clusters: $(get_all_clusters)"
        return 1
    fi

    echo "Setting up /etc/hosts entries for cluster: $cluster"
    echo "Hostnames: $hostnames"
    echo ""

    for hostname in $hostnames; do
        add_host_entry "$LOCALHOST" "$hostname" "$HOSTS_FILE"
    done

    echo ""
    echo "✓ Setup complete for cluster: $cluster"
}

# Function to verify entries
verify_entries() {
    local cluster=$1
    local hostnames

    hostnames=$(get_cluster_domains "$cluster")
    if [ $? -ne 0 ]; then
        return 1
    fi

    echo ""
    echo "Verifying /etc/hosts entries for cluster: $cluster"
    for hostname in $hostnames; do
        ip=$(grep "[[:space:]]$hostname$" "$HOSTS_FILE" | awk '{print $1}' | head -1)
        if [ -n "$ip" ]; then
            echo "✓ $ip $hostname"
        else
            echo "✗ Missing: $hostname"
        fi
    done
}

# Main logic
case "$CLUSTER_NAME" in
    all)
        echo "Setting up /etc/hosts for all clusters..."
        echo ""
        for cluster in $(get_all_clusters); do
            setup_cluster "$cluster"
            verify_entries "$cluster"
            echo ""
        done
        ;;
    help)
        cat << EOF
Usage: sudo $0 [cluster-name]

Setup /etc/hosts entries for OpenBacklog multi-cluster development.

Available clusters:
  dev
  agent-1
  agent-2
  agent-3

Examples:
  sudo $0 dev           # Setup dev cluster
  sudo $0 agent-1       # Setup agent-1 cluster
  sudo $0 all           # Setup all clusters
  sudo $0 help          # Show this help

The script will add entries like:
  127.0.0.1  dev.openbacklog.ai
  127.0.0.1  www.dev.openbacklog.ai

Edit get_cluster_domains() function to add/remove clusters.

Note: This script requires sudo to modify /etc/hosts
EOF
        ;;
    *)
        hostnames=$(get_cluster_domains "$CLUSTER_NAME")
        if [ $? -ne 0 ]; then
            echo "Error: Unknown cluster '$CLUSTER_NAME'"
            echo "Available clusters: $(get_all_clusters)"
            echo ""
            echo "Run 'sudo $0 help' for usage information"
            exit 1
        fi
        setup_cluster "$CLUSTER_NAME"
        verify_entries "$CLUSTER_NAME"
        ;;
esac

echo ""
echo "Next steps:"
cluster_domain=$(get_cluster_domains "$CLUSTER_NAME" | awk '{print $1}')
cluster_www_domain=$(get_cluster_domains "$CLUSTER_NAME" | awk '{print $2}')
echo "1. Create the cluster with:"
echo "   ./scripts/setup-cluster.sh create ${CLUSTER_NAME}"
echo ""
echo "2. Start the cluster with:"
echo "   cd docker && docker-compose --env-file .env.cluster-${CLUSTER_NAME} up -d"
echo ""
echo "3. Access the cluster:"

if [ "$CLUSTER_NAME" == "dev" ]; then
    echo "   http://${cluster_www_domain}/ (landing page, port 80)"
    echo "   http://${cluster_domain}/ (FastAPI, port 80)"
    echo ""
    echo "   Note: Dev cluster uses port 80, so no port number is needed in the URL"
else
    echo "   http://${cluster_domain}:81/ (FastAPI, port 81 for agent-1)"
    echo "   http://${cluster_www_domain}:81/ (landing page, port 81 for agent-1)"
    echo ""
    echo "   Note: Agent clusters require the port number in the URL because /etc/hosts"
    echo "   cannot specify ports - it only maps hostnames to IP addresses."
    echo ""
    echo "   Agent cluster port mapping:"
    echo "   - agent-1: http://agent-1.openbacklog.ai:81"
    echo "   - agent-2: http://agent-2.openbacklog.ai:82"
    echo "   - agent-3: http://agent-3.openbacklog.ai:83"
fi
