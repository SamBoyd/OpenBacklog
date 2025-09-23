-- Sentry Tunnel Validation Script
-- Implements the same validation logic as the JavaScript example
local cjson = require "cjson"

-- Get environment variables
local sentry_host = os.getenv("SENTRY_HOST") or "o4506167744266240.ingest.us.sentry.io"
local sentry_project_ids_str = os.getenv("SENTRY_PROJECT_IDS") or "4509116490776576"

-- Parse comma-separated project IDs into a set
local sentry_project_ids = {}
for project_id in string.gmatch(sentry_project_ids_str, "([^,]+)") do
    sentry_project_ids[string.gsub(project_id, "^%s*(.-)%s*$", "%1")] = true -- trim whitespace
end

-- Only allow POST requests
if ngx.var.request_method ~= "POST" then
    ngx.status = ngx.HTTP_METHOD_NOT_ALLOWED
    ngx.say('{"error": "Method not allowed"}')
    ngx.exit(ngx.HTTP_METHOD_NOT_ALLOWED)
end

-- Read the request body (envelope)
ngx.req.read_body()
local envelope_body = ngx.req.get_body_data()

-- If body data is not in memory, try to get it from temp file
if not envelope_body then
    local body_file = ngx.req.get_body_file()
    if body_file then
        local file = io.open(body_file, "r")
        if file then
            envelope_body = file:read("*all")
            file:close()
        end
    end
end

if not envelope_body then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say('{"error": "Empty request body"}')
    ngx.exit(ngx.HTTP_BAD_REQUEST)
end

-- Split envelope into lines and get the first line (header)
local lines = {}
for line in string.gmatch(envelope_body, "([^\n]*)\n?") do
    table.insert(lines, line)
end

if #lines == 0 then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say('{"error": "Invalid envelope format"}')
    ngx.exit(ngx.HTTP_BAD_REQUEST)
end

-- Parse the header (first line)
local header_line = lines[1]
local success, header = pcall(cjson.decode, header_line)

if not success or not header or not header.dsn then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say('{"error": "Invalid envelope header"}')
    ngx.exit(ngx.HTTP_BAD_REQUEST)
end

-- Parse the DSN URL
local dsn = header.dsn
local dsn_pattern = "https://([^@]+)@([^/]+)/(%d+)"
local key, hostname, project_id = string.match(dsn, dsn_pattern)

if not hostname or not project_id then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say('{"error": "Invalid DSN format"}')
    ngx.exit(ngx.HTTP_BAD_REQUEST)
end

-- Validate hostname
if hostname ~= sentry_host then
    ngx.status = ngx.HTTP_FORBIDDEN
    ngx.say('{"error": "Invalid sentry hostname: ' .. hostname .. '"}')
    ngx.exit(ngx.HTTP_FORBIDDEN)
end

-- Validate project ID
if not sentry_project_ids[project_id] then
    ngx.status = ngx.HTTP_FORBIDDEN
    ngx.say('{"error": "Invalid sentry project id: ' .. project_id .. '"}')
    ngx.exit(ngx.HTTP_FORBIDDEN)
end

-- Construct upstream URL
local upstream_url = "https://" .. sentry_host .. "/api/" .. project_id .. "/envelope/"

-- Set variables for the proxy pass
ngx.var.upstream_uri = upstream_url
ngx.var.upstream_host = sentry_host