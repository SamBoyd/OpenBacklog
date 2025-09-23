FROM python:3.12.7-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create jovyan user (matching Jupyter convention)
RUN useradd -m -u 1000 jovyan
USER jovyan
WORKDIR /home/jovyan

# Install Jupyter Lab and common scientific packages
RUN pip install -U --no-cache-dir \
    jupyterlab \
    numpy \
    pandas \
    matplotlib \
    scipy \
    seaborn

# Copy requirements and install project dependencies
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Set Python path to include the src directory from the mounted volume
ENV PYTHONPATH="/home/jovyan/work/src:${PYTHONPATH}"

# Expose Jupyter port
EXPOSE 8888

ENV PATH="/home/jovyan/.local/bin:${PATH}"

# Start Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=", "--NotebookApp.password="]