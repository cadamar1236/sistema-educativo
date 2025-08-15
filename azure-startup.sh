#!/bin/bash

# Azure App Service Comprehensive Startup Script
# Includes dependency installation and optimization

echo "=========================================="
echo "Azure App Service - Full Startup Script"
echo "=========================================="

# Environment setup
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-4}

# Log startup time
START_TIME=$(date +%s)

echo "[1/6] System Information:"
echo "Python: $(python --version)"
echo "Port: ${PORT}"
echo "Workers: ${WORKERS}"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "CPU: $(nproc) cores"

echo "[2/6] Installing system dependencies..."
# Install Tesseract OCR if not present
if ! command -v tesseract &> /dev/null; then
    apt-get update -qq && apt-get install -y -qq tesseract-ocr tesseract-ocr-eng 2>/dev/null || {
        echo "Warning: Could not install Tesseract OCR"
    }
fi

echo "[3/6] Installing Python dependencies..."
# Install requirements with optimization flags
if [ -f "requirements-azure.txt" ]; then
    pip install --no-cache-dir -r requirements-azure.txt 2>/dev/null || {
        echo "Warning: Some dependencies failed to install"
    }
elif [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || {
        echo "Warning: Some dependencies failed to install"
    }
fi

echo "[4/6] Setting up application structure..."
# Ensure necessary directories exist
mkdir -p data/library data/chroma_db logs

# Create optimized Gunicorn configuration
cat > gunicorn_config.py << 'EOF'
import multiprocessing
import os

# Bind to Azure port
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"

# Worker configuration
workers = int(os.environ.get('WORKERS', min(multiprocessing.cpu_count() * 2 + 1, 4)))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
threads = 2

# Timeout and keepalive
timeout = 120
graceful_timeout = 30
keepalive = 5

# Preloading
preload_app = True

# Restart workers periodically to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# StatsD (optional)
statsd_host = os.environ.get('STATSD_HOST')
if statsd_host:
    statsd_prefix = 'julia_ai'
EOF

echo "[5/6] Optimizing for Azure..."
# Azure-specific optimizations
if [ "$WEBSITE_INSTANCE_ID" ]; then
    echo "Running on Azure App Service instance: $WEBSITE_INSTANCE_ID"
    
    # Use Azure temp directory for faster I/O
    export TMPDIR=/tmp
    
    # Optimize Python for Azure
    export PYTHONHASHSEED=0
    
    # Set thread pool size for better concurrency
    export UVICORN_WORKER_THREADS=2
fi

# Calculate startup time
CURRENT_TIME=$(date +%s)
ELAPSED=$((CURRENT_TIME - START_TIME))
echo "Setup completed in ${ELAPSED} seconds"

echo "[6/6] Starting application server..."
echo "=========================================="
echo "Server starting on http://0.0.0.0:${PORT}"
echo "Workers: ${WORKERS}"
echo "=========================================="

# Health check endpoint test
python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.main_simple import app
    print('✓ Application loaded successfully')
except Exception as e:
    print(f'✗ Application load error: {e}')
    sys.exit(1)
"

# Start application with Gunicorn
if [ -f "src/main_simple.py" ]; then
    exec gunicorn src.main_simple:app --config gunicorn_config.py
elif [ -f "main.py" ]; then
    exec gunicorn main:app --config gunicorn_config.py
else
    echo "Error: Could not find application entry point"
    echo "Falling back to development server..."
    exec python -m uvicorn src.main_simple:app --host 0.0.0.0 --port ${PORT}
fi