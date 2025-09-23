# Use the official HashiCorp Vault image
FROM hashicorp/vault:1.19.1

# Vault configuration directory
ENV VAULT_CONFIG_DIR=/vault/config
ENV VAULT_DATA_DIR=/vault/data
ENV VAULT_CERTS_DIR=/vault/certs

# Expose the Vault ports (8200 for API, 8201 for cluster)
# IMPORTANT: Do not expose these ports directly to the public internet without
# proper security measures like network policies, firewalls, and TLS.
EXPOSE 8200 8201

# Copy all configuration files
COPY ./docker/vault-dev.hcl /vault/config/vault-dev.hcl
COPY ./docker/vault-preprod.hcl /vault/config/vault-preprod.hcl  
COPY ./docker/vault-prod.hcl /vault/config/vault-prod.hcl

# Create a startup script
COPY <<EOF /usr/local/bin/docker-entrypoint.sh
#!/bin/sh
set -e

# Fail if VAULT_ENVIRONMENT is not set
if [ -z "\$VAULT_ENVIRONMENT" ]; then
    echo "Error: VAULT_ENVIRONMENT environment variable must be set!"
    echo "Valid values: dev, preprod, prod"
    exit 1
fi

# Create directories with appropriate permissions
mkdir -p \${VAULT_CONFIG_DIR}
mkdir -p \${VAULT_DATA_DIR}
mkdir -p \${VAULT_CERTS_DIR}

# Select configuration file based on environment
CONFIG_FILE="\${VAULT_CONFIG_DIR}/vault-\${VAULT_ENVIRONMENT}.hcl"

if [ ! -f "\$CONFIG_FILE" ]; then
    echo "Error: Configuration file \$CONFIG_FILE not found!"
    echo "Available configurations:"
    ls -la \${VAULT_CONFIG_DIR}/vault-*.hcl
    exit 1
fi

echo "Starting Vault with environment: \$VAULT_ENVIRONMENT"
echo "Using configuration: \$CONFIG_FILE"

# Set appropriate permissions for writable directories
chown -R vault:vault \${VAULT_CONFIG_DIR} \${VAULT_DATA_DIR}

# For dev environment, skip TLS certificate check
if [ "\$VAULT_ENVIRONMENT" = "dev" ]; then
    echo "Development mode: TLS disabled"
else
    # Check if certificates exist for non-dev environments
    # First check Render secrets location, then fallback to local certs directory
    if [ -f "/etc/secrets/vault_listener_cert.pem" ] && [ -f "/etc/secrets/vault_listener_key.pem" ]; then
        echo "TLS certificates found in Render secrets, enabling HTTPS"
    elif [ -f "\${VAULT_CERTS_DIR}/vault-cert.pem" ] && [ -f "\${VAULT_CERTS_DIR}/vault-key.pem" ]; then
        echo "TLS certificates found in local certs directory, enabling HTTPS"
    else
        echo "Warning: TLS certificates not found"
        echo "Expected files (Render):"
        echo "  - /etc/secrets/vault_listener_cert.pem"
        echo "  - /etc/secrets/vault_listener_key.pem"
        echo "Expected files (Local):"
        echo "  - \${VAULT_CERTS_DIR}/vault-cert.pem"
        echo "  - \${VAULT_CERTS_DIR}/vault-key.pem"
        echo ""
        echo "For local development: scripts/generate-vault-certs.sh \$VAULT_ENVIRONMENT"
        echo "For Render deployment: Upload certificates as secret files"
        exit 1
    fi
fi

# Create runtime config by substituting environment variables
RUNTIME_CONFIG_FILE="\${VAULT_CONFIG_DIR}/vault-\${VAULT_ENVIRONMENT}-runtime.hcl"
cp "\$CONFIG_FILE" "\$RUNTIME_CONFIG_FILE"

# Perform environment variable substitutions for production config
if [ "\$VAULT_ENVIRONMENT" = "prod" ]; then
    # Set default cluster address if not provided
    VAULT_CLUSTER_ADDR=\${VAULT_CLUSTER_ADDR:-"https://\$(hostname):8201"}
    
    echo "Configuring cluster address: \$VAULT_CLUSTER_ADDR"
    
    # Replace placeholder with actual cluster address
    sed -i "s|VAULT_CLUSTER_ADDR_PLACEHOLDER|\$VAULT_CLUSTER_ADDR|g" "\$RUNTIME_CONFIG_FILE"
    
    # Verify substitution was successful
    if grep -q "VAULT_CLUSTER_ADDR_PLACEHOLDER" "\$RUNTIME_CONFIG_FILE"; then
        echo "Error: Failed to substitute VAULT_CLUSTER_ADDR_PLACEHOLDER"
        exit 1
    fi
    
    echo "Configuration substitution completed successfully"
fi

# Start vault with runtime config
exec vault server -config="\$RUNTIME_CONFIG_FILE"
EOF

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Healthcheck to verify Vault is running (optional but recommended)
HEALTHCHECK --interval=5s --timeout=3s \
  CMD if [ "$VAULT_ENVIRONMENT" = "dev" ]; then \
        curl --fail http://127.0.0.1:8200/v1/sys/health?standbyok=true; \
      else \
        curl --fail --insecure https://127.0.0.1:8200/v1/sys/health?standbyok=true; \
      fi

# Note on Security:
# - Configure TLS for all communication with Vault.
# - Use a production-ready storage backend (e.g., Consul, Integrated Storage/Raft).
# - Implement strict access control policies (ACLs).
# - Regularly rotate secrets and audit access logs.
