# Multi-stage Dockerfile for lightweight production image
# Stage 1: Builder - compile dependencies
FROM python:3.10-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --user --no-warn-script-location \
    -r requirements.txt

# Stage 2: Runtime - minimal production image
FROM python:3.10-alpine

WORKDIR /app

# Install only runtime dependencies
RUN apk add --no-cache \
    curl \
    tini

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_PATH=/data/identity.db

# Create data directory for SQLite database
RUN mkdir -p /data

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/auth/validate || exit 1

# Use tini as PID 1 for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start FastAPI application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
