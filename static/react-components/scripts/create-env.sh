#!/bin/bash

# Create environment file from environment variables for builds
# Usage: ./create-env.sh <environment> (e.g., prod, preprod)

if [ $# -eq 0 ]; then
    echo "Usage: $0 <environment>"
    echo "Example: $0 prod"
    echo "Example: $0 preprod"
    exit 1
fi

ENVIRONMENT=$1
EXAMPLE_FILE="static/react-components/.env.example"
ENV_FILE="static/react-components/.env.${ENVIRONMENT}"

echo "Creating .env.${ENVIRONMENT} from environment variables based on .env.example..."

# Check if .env.example exists
if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "Error: $EXAMPLE_FILE not found"
    exit 1
fi

# Remove existing env file if it exists
rm -f "$ENV_FILE"

# Read each line from .env.example and create corresponding entries
while IFS= read -r line; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # Extract variable name (handle cases with or without = and values)
    var_name=$(echo "$line" | cut -d'=' -f1 | tr -d '[:space:]')

    # Skip if variable name is empty
    if [[ -z "$var_name" ]]; then
        continue
    fi

    # Get the value from environment variable
    var_value="${!var_name}"

    # Write to env file
    echo "${var_name}=${var_value}" >> "$ENV_FILE"

    if [[ -n "$var_value" ]]; then
        echo "✓ Set ${var_name}"
    else
        echo "⚠ Warning: ${var_name} is empty or not set"
    fi

done < "$EXAMPLE_FILE"

echo ".env.${ENVIRONMENT} created successfully"