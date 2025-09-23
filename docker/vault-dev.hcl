api_addr                = "http://0.0.0.0:8200"
cluster_addr            = "http://0.0.0.0:8201"
cluster_name            = "preprodvault"
disable_mlock           = true
ui                      = false
default_lease_ttl       = "168h"
max_lease_ttl          = "720h"


listener "tcp" {
    address     = "0.0.0.0:8200"
    tls_disable = true
}

storage "raft" {
    path    = "/vault"
    node_id = "node1"
}
