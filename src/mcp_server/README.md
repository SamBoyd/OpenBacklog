To connect this mcp server with claude code run 

```bash
claude mcp add \
    -H"Authorization: Bearer XXXX" \
    -H"X-Workspace-Id: XXXX" \
    --transport=http \
    openbacklog \
    http://127.0.0.1:9000/mcp
```