# Use the stable litellm release
FROM litellm/litellm:v1.74.9-stable.patch.1


# Set the working directory to /app
WORKDIR /app

# Copy the configuration file to the correct location
COPY config/litellm/config.yaml .

# Make sure docker/entrypoint.sh is executable
RUN chmod +x ./docker/entrypoint.sh

# Expose the necessary port
EXPOSE 4000/tcp

CMD ["--port", "4000", "--config", "config.yaml"]
