# Use the official Python 3.12 image
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY src/mcp_server/requirements.txt .

# Install Python dependencies
# Upgrade pip first
RUN pip install --no-cache-dir -U --upgrade pip

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs
EXPOSE 9000

# Set Python path to include the current directory
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Use the startup script (path adjusted for volume mount) to run migrations and then start the app
CMD ["python", "-m", "src.mcp_server.main"]
