# ============================================================================
# Stage 1: Build React Components
# ============================================================================
FROM node:18-alpine AS react-builder

WORKDIR /app/static/react-components

# Copy package files
COPY static/react-components/package*.json ./

# Install dependencies
RUN npm install

# Copy React source code and cluster-specific env file
COPY static/react-components .

# Build argument for cluster name (used to load .env.cluster-{name})
ARG CLUSTER_NAME=dev
ENV CLUSTER_NAME=$CLUSTER_NAME

RUN rm .env.*
# Copy cluster-specific environment file from project root
# This allows webpack to load .env.cluster-{CLUSTER_NAME} during the build
COPY static/react-components/.env.cluster-${CLUSTER_NAME} .env.cluster-${CLUSTER_NAME}

# Build React components (webpack will load .env.cluster-{CLUSTER_NAME})
RUN npm run tailwind
RUN npm run scss
RUN npm run build:dev

# ============================================================================
# Stage 2: Build Python FastAPI Application with React Assets
# ============================================================================
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm versions
RUN node -v
RUN npm -v

# Copy the requirements file into the container
COPY requirements.txt .

# install git to be able to install the fastmcp from the git repository
RUN apt-get update && apt-get install -y git

# Install Python dependencies
# Upgrade pip first
RUN pip install --no-cache-dir -U --upgrade pip
# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install fastmcp from the git repository
# RUN pip install --no-cache-dir git+https://github.com/jlowin/fastmcp.git@f8b896490e95cdec0f581ec1154a767c69c069cf

# Copy Python source and other files (excluding react-components source)
# This allows React-only changes to not invalidate these layers
COPY src/ ./src/
COPY templates/ ./templates/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY docker/ ./docker/

# Copy static assets (excluding react-components source - we get build from react-builder)
COPY static/css/ ./static/css/
COPY static/github-mark/ ./static/github-mark/
COPY static/*.png ./static/
COPY static/*.svg ./static/

# Copy root-level build files
COPY package.json package-lock.json ./
COPY webpack.config.js tailwind.config.js postcss.config.js ./

COPY .env* ./

# Build argument for cluster name (used to load .env.cluster-{name})
ARG CLUSTER_NAME=dev
ENV CLUSTER_NAME=$CLUSTER_NAME
COPY .env.cluster-${CLUSTER_NAME}* .env
COPY .env.development* .env

# Build the static assets
RUN npm install
RUN npm run build

# Copy React build artifacts from Stage 1
# We copy specific build artifacts to ensure they're properly included
COPY --from=react-builder /app/static/react-components/build/ ./static/react-components/build/
COPY --from=react-builder /app/static/react-components/node_modules/ ./static/react-components/node_modules/
COPY --from=react-builder /app/static/react-components/webpack-assets.json ./static/react-components/webpack-assets.json

# Expose the port the app runs on (default for uvicorn is 8000)
EXPOSE 8000

ENV FASTMCP_SERVER_AUTH_AUTH0_REQUIRED_SCOPES "openid profile email offline_access"

# Use the startup script (path adjusted for volume mount) to run migrations and then start the app
CMD ["/app/docker/start.sh", "--reload"]
