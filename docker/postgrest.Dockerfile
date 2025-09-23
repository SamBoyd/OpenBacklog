# Use the official PostgreSQL image
# Consider pinning to a specific major version (e.g., postgres:16) for stability
FROM postgrest/postgrest:v12.2.8

ENV PGRST_SERVER_PORT $PORT

EXPOSE $PGRST_SERVER_PORT

CMD ["/bin/postgrest"]