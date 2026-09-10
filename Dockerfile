# ==============================================================================
# Stage 1: Build virtual environment & install Python dependencies
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies if needed and create virtual environment
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Final Production Runtime Image
# ==============================================================================
FROM python:3.12-slim AS runner

WORKDIR /app

# Set Python production runtime flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Install curl for Docker health checks & clean apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-privileged user and group (appuser: 10001) and storage directories
RUN groupadd -g 10001 appuser \
    && useradd -u 10001 -g appuser -s /bin/sh -m appuser \
    && mkdir -p /app/data/uploads/avatars \
    && chown -R appuser:appuser /app

# Copy application code with non-root ownership
COPY --chown=appuser:appuser app ./app

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8000

# Native container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start production ASGI server with proxy headers enabled (for Caddy/Nginx reverse proxies)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
