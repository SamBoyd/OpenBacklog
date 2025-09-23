api_addr                = "https://0.0.0.0:8200"
cluster_addr            = "https://taskmanagement-d28a:8201"
cluster_name            = "preprod-vault"
disable_mlock           = true
ui                      = false
default_lease_ttl       = "168h"
max_lease_ttl          = "720h"


listener "tcp" {
    address       = "0.0.0.0:8200"
    tls_cert_file = "/etc/secrets/vault_listener_cert.pem"
    tls_key_file  = "/etc/secrets/vault_listener_key.pem"
    tls_min_version = "tls12"
}

listener "tcp" {
    address       = "0.0.0.0:8201"
    tls_cert_file = "/etc/secrets/vault_listener_cert.pem"
    tls_key_file  = "/etc/secrets/vault_listener_key.pem"
    tls_min_version = "tls12"
    cluster_address = "0.0.0.0:8201"
}

storage "raft" {
    path    = "/vault"
    node_id = "node1"
}
