# Railway Dockerfile for SeenSlide Cloud Server
FROM python:3.12-slim

# Install system dependencies for compiling Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Start command
CMD python -m modules.cloud.server --host 0.0.0.0 --port ${PORT:-8000}
