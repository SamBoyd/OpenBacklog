# Dockerfile for Analytics Proxy Service
# Single Nginx instance to proxy both Sentry and Mixpanel traffic
# Supports environment variable templating for domain configuration

FROM openresty/openresty:alpine

# Install gettext for envsubst command and CA certificates for SSL verification
RUN apk add --no-cache gettext ca-certificates

# Copy the templated nginx configuration and Lua script
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf.template
COPY sentry_tunnel.lua /usr/local/openresty/nginx/conf/sentry_tunnel.lua

# Expose port 80 (Render handles SSL termination)
EXPOSE 80

# Add labels for better container management
LABEL maintainer="OpenBacklog Team"
LABEL description="Self-hosted analytics proxy for Sentry and Mixpanel"
LABEL version="1.0.0"

# Set default environment variables
ENV SENTRY_DOMAIN=sentry.openbacklog.ai
ENV MIXPANEL_DOMAIN=mixpanel.openbacklog.ai
ENV SENTRY_HOST=o4506167744266240.ingest.us.sentry.io
ENV SENTRY_PROJECT_IDS=4509116490776576

# Create startup script that templates the nginx config
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'envsubst "\$SENTRY_DOMAIN \$MIXPANEL_DOMAIN \$SENTRY_HOST \$SENTRY_PROJECT_IDS" < /usr/local/openresty/nginx/conf/nginx.conf.template > /usr/local/openresty/nginx/conf/nginx.conf' >> /docker-entrypoint.sh && \
    echo 'exec openresty -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Use custom entrypoint that templates config before starting nginx
CMD ["/docker-entrypoint.sh"]