# Use the official Python 3.12 image
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# Upgrade pip first
RUN pip install --no-cache-dir -U --upgrade pip
# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create and set permissions for the startup script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the port the app runs on (default for uvicorn is 8000)
EXPOSE 8000

# Use the startup script (path adjusted for volume mount) to run migrations and then start the app
CMD ["/app/docker/start.sh", "--reload"]
