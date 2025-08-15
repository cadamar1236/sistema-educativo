#!/bin/bash

# Azure App Service Ultra-Fast Startup Script
# Target: 10-15 second initialization time
# Uses Gunicorn with Uvicorn workers for optimal performance

echo "=========================================="
echo "Azure App Service - Quick Start (10-15s)"
echo "=========================================="

# Set environment variables for optimal performance
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PORT=${PORT:-8000}

# Log startup time
START_TIME=$(date +%s)

echo "[1/4] Setting up Python environment..."
# Skip pip upgrade to save time
# Use --no-cache-dir to avoid cache operations

# Only install critical missing packages (if any)
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing critical dependencies..."
    pip install --no-cache-dir fastapi uvicorn gunicorn pytesseract 2>/dev/null || true
fi

echo "[2/4] Configuring application..."
# Create minimal gunicorn config for fast startup
cat > /tmp/gunicorn_conf.py << 'EOF'
import multiprocessing

# Optimize for Azure App Service
bind = "0.0.0.0:8000"
workers = 2  # Minimal workers for fast startup
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5

# Fast startup settings
preload_app = True  # Preload app for faster worker startup
timeout = 120
graceful_timeout = 30

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Performance
max_requests = 1000
max_requests_jitter = 50
EOF

echo "[3/4] Starting application server..."

# Calculate elapsed time
CURRENT_TIME=$(date +%s)
ELAPSED=$((CURRENT_TIME - START_TIME))
echo "Setup completed in ${ELAPSED} seconds"

echo "[4/4] Launching Gunicorn with Uvicorn workers..."
echo "Server will be available at http://0.0.0.0:${PORT}"

# Start with Gunicorn using minimal workers and preloading
# This provides the fastest possible startup time
exec gunicorn src.main_simple:app \
    --config /tmp/gunicorn_conf.py \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 0.0.0.0:${PORT} \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info

# Alternative ultra-fast single-worker mode (if above fails)
# exec python -m uvicorn src.main_simple:app --host 0.0.0.0 --port ${PORT} --workers 1