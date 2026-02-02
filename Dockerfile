# EstradaBot - Production Dockerfile for Google Cloud Run
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY backend/ ./backend/

# Create directories for runtime data
RUN mkdir -p "./Scheduler Bot Info" "./outputs"

# Set environment variables
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD ["sh", "-c", "gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 backend.app:app"]
