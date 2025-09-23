# Use the official stable Nginx image based on Alpine Linux
FROM nginx:stable-alpine

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom Nginx configuration file
# Use absolute path to ensure proper loading
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# For extra certainty, also place it in the main config location
# This ensures our config will be used
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Create directory for static files
RUN mkdir -p /usr/share/nginx/html/static
RUN mkdir -p /usr/share/nginx/html/js

# Fix relative paths in COPY commands
# The "../" is incorrect in a Docker build context
COPY static /usr/share/nginx/html/static
RUN rm -rf /usr/share/nginx/html/static/react-components

# Fix path for react components
COPY static/react-components/build /usr/share/nginx/html/js

# Expose port 80 for HTTP traffic
EXPOSE 80

# The base image already defines the CMD ["nginx", "-g", "daemon off;"]
# No need to redefine it unless customization is needed.
