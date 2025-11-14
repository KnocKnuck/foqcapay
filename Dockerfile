# Multi-stage Dockerfile for FOQCAPAY Trading Bot
# Sprint: 5.2
# Optimized for production deployment

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Create app user for security
RUN useradd -m -u 1000 foqcapay && \
    mkdir -p /app /app/data /app/logs && \
    chown -R foqcapay:foqcapay /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/foqcapay/.local

# Copy application code
COPY --chown=foqcapay:foqcapay backend/ /app/

# Set Python path
ENV PATH=/home/foqcapay/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to app user
USER foqcapay

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
