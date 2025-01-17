# Use Python 3.10 slim as a base
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for browser-use (e.g. Chrome dependencies if needed).
# For a minimal Docker image, we may rely on the host system or a separate container
# to run an actual Chrome or Chromium instance. Adjust as needed if you want a fully
# contained browser environment.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install python dependencies, including browser-use
RUN pip install --no-cache-dir .

# Expose the default port
EXPOSE 8031

CMD ["python", "-m", "my_mcp_server.main"]