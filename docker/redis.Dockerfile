FROM redis:7-alpine

# Install gettext for envsubst
RUN apk add --no-cache gettext

RUN mkdir -p /usr/local/etc/
RUN mkdir -p /usr/local/bin/

# Copy Redis configuration and scripts
COPY ./redis.conf /usr/local/etc/redis/redis.conf
COPY ./redis-init.sh /usr/local/bin/redis-init.sh
COPY ./redis-entrypoint.sh /usr/local/bin/redis-entrypoint.sh

# Make scripts executable
RUN chmod +x /usr/local/bin/redis-init.sh 
RUN chmod +x /usr/local/bin/redis-entrypoint.sh

# Use our custom entrypoint
ENTRYPOINT ["/usr/local/bin/redis-entrypoint.sh"] 