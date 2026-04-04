FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright for some checks (optional)
RUN playwright install-deps chromium || true
RUN playwright install chromium || true

# Copy application code
COPY . .

# Create jobs directory
RUN mkdir -p /tmp/fast_jobs

# Expose port
EXPOSE 8001

# Start server with multiple workers for massive processing
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
