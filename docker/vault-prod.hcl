api_addr                = "https://0.0.0.0:8200"
cluster_addr            = "VAULT_CLUSTER_ADDR_PLACEHOLDER"
cluster_name            = "prod-vault"
disable_mlock           = true
ui                      = false
default_lease_ttl       = "168h"
max_lease_ttl          = "720h"

listener "tcp" {
    address       = "0.0.0.0:8200"
    tls_cert_file = "/etc/secrets/vault_listener_cert.pem"
    tls_key_file  = "/etc/secrets/vault_listener_key.pem"
    tls_min_version = "tls12"
    tls_cipher_suites = "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
}

listener "tcp" {
    address       = "0.0.0.0:8201"
    tls_cert_file = "/etc/secrets/vault_listener_cert.pem"
    tls_key_file  = "/etc/secrets/vault_listener_key.pem"
    tls_min_version = "tls12"
    tls_cipher_suites = "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
    cluster_address = "0.0.0.0:8201"
}

storage "raft" {
    path    = "/vault/data"
    node_id = "node1"
}