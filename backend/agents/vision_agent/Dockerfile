# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY vision_agent.py .
COPY app.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the application
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT}

# export GCP_PROJECT_ID="adsp-34002-ip07-visionary-ai" 
# export GCP_REGION="us-central1"

# # Make deployment script executable
# chmod +x deploy.sh

# # Run deployment (this takes 5-10 minutes)
# ./deploy.sh


