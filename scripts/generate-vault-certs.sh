#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VAULT_CERTS_DIR="$PROJECT_ROOT/vault/certs"

# Parse arguments
ENVIRONMENT=""
VAULT_HOSTNAME=""
USE_CERTBOT=false
RENEW=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --certbot)
            USE_CERTBOT=true
            shift
            ;;
        --renew)
            RENEW=true
            shift
            ;;
        preprod|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            if [[ -z "$VAULT_HOSTNAME" ]]; then
                VAULT_HOSTNAME="$1"
            else
                echo "Unknown argument: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Set defaults
ENVIRONMENT="${ENVIRONMENT:-preprod}"
VAULT_HOSTNAME="${VAULT_HOSTNAME:-localhost}"

if [[ "$ENVIRONMENT" != "preprod" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Usage: $0 [preprod|prod] [hostname] [--certbot] [--renew]"
    echo "Examples:"
    echo "  $0 preprod vault-preprod.example.com --certbot"
    echo "  $0 prod vault.example.com --certbot"
    echo "  $0 prod vault.example.com --certbot --renew"
    echo "  $0 preprod  # generates self-signed cert for localhost"
    exit 1
fi

echo "Generating Vault TLS certificates for $ENVIRONMENT environment..."
echo "Hostname: $VAULT_HOSTNAME"
echo "Use Certbot: $USE_CERTBOT"
echo "Renew: $RENEW"

mkdir -p "$VAULT_CERTS_DIR"
cd "$VAULT_CERTS_DIR"

if [[ "$USE_CERTBOT" == "true" ]]; then
    # Certbot certificate generation using DNS challenge
    echo "Using certbot to generate Let's Encrypt certificates via DNS challenge..."
    
    # Validate hostname is not localhost for certbot
    if [[ "$VAULT_HOSTNAME" == "localhost" ]]; then
        echo "Error: Cannot use certbot with localhost. Please provide a valid domain name."
        echo "Example: $0 $ENVIRONMENT vault-$ENVIRONMENT.example.com --certbot"
        exit 1
    fi
    
    # Set Let's Encrypt server based on environment
    if [[ "$ENVIRONMENT" == "preprod" ]]; then
        LE_SERVER="--staging"
        echo "Using Let's Encrypt staging environment for preprod"
    else
        LE_SERVER=""
        echo "Using Let's Encrypt production environment"
    fi
    
    # Docker command for certbot with manual DNS challenge
    CERTBOT_CMD="docker run -it --rm --name certbot \
        -v \"$VAULT_CERTS_DIR:/etc/letsencrypt\" \
        -v \"$VAULT_CERTS_DIR:/var/lib/letsencrypt\" \
        certbot/certbot"
    
    if [[ "$RENEW" == "true" ]]; then
        echo "Renewing certificate for $VAULT_HOSTNAME..."
        echo "Note: You may need to update DNS TXT records again during renewal."
        eval "$CERTBOT_CMD renew --manual --preferred-challenges dns $LE_SERVER"
    else
        echo "Obtaining new certificate for $VAULT_HOSTNAME using manual DNS challenge..."
        echo ""
        echo "IMPORTANT: You will be prompted to create DNS TXT records."
        echo "Have access to your DNS provider ready:"
        if [[ "$VAULT_HOSTNAME" == *"samboyd.dev"* ]]; then
            echo "- SquareSpace DNS management for samboyd.dev"
        elif [[ "$VAULT_HOSTNAME" == *"openbacklog.ai"* ]]; then
            echo "- GoDaddy DNS management for openbacklog.ai"
        else
            echo "- Your DNS provider management interface"
        fi
        echo ""
        read -p "Press Enter when ready to continue..."
        
        eval "$CERTBOT_CMD certonly --manual --preferred-challenges dns $LE_SERVER --agree-tos --no-eff-email --email admin@$VAULT_HOSTNAME -d $VAULT_HOSTNAME"
    fi
    
    # Copy certificates to expected location
    if [[ -d "live/$VAULT_HOSTNAME" ]]; then
        echo "Copying certificates to vault expected locations..."
        cp "live/$VAULT_HOSTNAME/fullchain.pem" vault-cert.pem
        cp "live/$VAULT_HOSTNAME/privkey.pem" vault-key.pem
        
        chmod 444 vault-cert.pem
        chmod 400 vault-key.pem
        
        echo "Certbot certificates successfully generated and copied!"
        echo ""
        echo "IMPORTANT: Save the DNS TXT records you created for future renewals."
    else
        echo "Error: Certificate directory not found. Certbot may have failed."
        exit 1
    fi
    
elif [[ "$ENVIRONMENT" == "preprod" ]]; then
    echo "Generating self-signed certificates for preprod..."
    
    cat > vault-cert.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = TaskManagement
OU = IT Department
CN = $VAULT_HOSTNAME

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $VAULT_HOSTNAME
DNS.2 = localhost
DNS.3 = vault
DNS.4 = taskmanagement-d28a
IP.1 = 127.0.0.1
IP.2 = 0.0.0.0
EOF

    openssl genrsa -out vault-key.pem 4096
    
    openssl req -new -key vault-key.pem -out vault.csr -config vault-cert.conf
    
    openssl x509 -req -in vault.csr -signkey vault-key.pem -out vault-cert.pem \
        -days 365 -extensions v3_req -extfile vault-cert.conf
    
    rm vault.csr vault-cert.conf
    
    echo "Self-signed certificates generated successfully!"
    
elif [[ "$ENVIRONMENT" == "prod" ]]; then
    echo "Production certificate generation has multiple options:"
    echo ""
    echo "RECOMMENDED: Use --certbot flag for Let's Encrypt certificates:"
    echo "  $0 prod $VAULT_HOSTNAME --certbot"
    echo ""
    echo "ALTERNATIVE: Manual CA-signed certificates:"
    echo "1. Generate a private key:"
    echo "   openssl genrsa -out vault-key.pem 4096"
    echo ""
    echo "2. Generate a Certificate Signing Request (CSR):"
    echo "   openssl req -new -key vault-key.pem -out vault.csr -subj \"/CN=$VAULT_HOSTNAME\""
    echo ""
    echo "3. Submit the CSR to your Certificate Authority"
    echo ""
    echo "4. Place the signed certificate in this directory as 'vault-cert.pem'"
    echo ""
    echo "5. Ensure the certificate chain includes any intermediate certificates"
    echo ""
    exit 0
fi

# Only set permissions and show details if certificates were actually generated
if [[ -f "vault-key.pem" && -f "vault-cert.pem" ]]; then
    chmod 400 vault-key.pem
    chmod 444 vault-cert.pem

    echo ""
    echo "Certificate files created:"
    echo "  Private key: $VAULT_CERTS_DIR/vault-key.pem"
    echo "  Certificate: $VAULT_CERTS_DIR/vault-cert.pem"
    echo ""
    echo "Certificate details:"
    openssl x509 -in vault-cert.pem -text -noout | grep -A 1 "Subject:"
    openssl x509 -in vault-cert.pem -text -noout | grep -A 1 "Validity"
    openssl x509 -in vault-cert.pem -text -noout | grep -A 5 "Subject Alternative Name"

    echo ""
    echo "Certificate expiration check:"
    echo "  openssl x509 -in vault-cert.pem -noout -dates"
    
    if [[ "$USE_CERTBOT" == "true" ]]; then
        echo ""
        echo "To renew the certificate before expiration:"
        echo "  $0 $ENVIRONMENT $VAULT_HOSTNAME --certbot --renew"
    else
        echo ""
        echo "To verify the certificate:"
        echo "  openssl verify -CAfile vault-cert.pem vault-cert.pem"
    fi
fi