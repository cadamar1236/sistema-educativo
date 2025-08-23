# =============================================================================
# DOCKERFILE COMPLETO PARA SISTEMA EDUCATIVO
# Frontend (Next.js) + Backend (FastAPI) en una sola imagen
# =============================================================================

# Stage 1: Build del Frontend Next.js
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# Asegurar carpeta public (el proyecto actual no tiene /public en repo y el COPY final falla)
RUN mkdir -p public && echo "placeholder" > public/.placeholder

# Copiar package.json primero para aprovechar cache de Docker
COPY julia-frontend/package.json julia-frontend/package*.json ./

# Instalar dependencias del frontend
RUN npm install

# Copiar archivos de configuración
COPY julia-frontend/next.config.js ./
COPY julia-frontend/tailwind.config.ts ./
COPY julia-frontend/tsconfig.json ./
COPY julia-frontend/postcss.config.js ./

# Copiar todo el código del frontend
COPY julia-frontend/ ./

ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NODE_ENV=production
# Build: con output:'export' en next.config.js, 'npm run build' genera directamente 'out/'
RUN npm run build

# Stage 2: Backend Python con Frontend estático
FROM python:3.11-slim AS production

# Variables de sistema
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Instalar dependencias del sistema
# Añadimos nginx y supervisor para servir frontend + proxy API
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gcc \
    g++ \
    build-essential \
    nginx \
    supervisor \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copiar y instalar dependencias Python
COPY requirements.txt requirements*.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Crear estructura de directorios
RUN mkdir -p \
    /app/data/uploads \
    /app/data/temp \
    /app/data/reports \
    /app/logs \
    /app/static \
    /app/static/frontend

# Copiar código del backend
COPY src/ ./src/
COPY agents/ ./agents/
COPY *.py ./

# Copiar archivos de configuración
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Copiar sitio estático exportado (lo necesita FastAPI y también lo servirá Nginx)
COPY --from=frontend-builder /frontend/out/ ./static/
RUN mkdir -p /usr/share/nginx/html && cp -R ./static/* /usr/share/nginx/html/

# Copiar configs de Nginx y Supervisor (si existen del repo) o crear fallback mínimos
COPY nginx/fullstack.conf /etc/nginx/conf.d/default.conf
COPY supervisord.single.conf /etc/supervisor/conf.d/supervisord.conf

# Fallback simple si no se copiaron (evitar fallo build) - crea index de placeholder
RUN [ -f /etc/nginx/conf.d/default.conf ] || echo 'server { listen 80; root /usr/share/nginx/html; location /api/ { proxy_pass http://127.0.0.1:8001/; } }' > /etc/nginx/conf.d/default.conf

# (Opcional) Si se cambiara a modo no-export, se podría copiar sólo los assets:
# COPY --from=frontend-builder /frontend/.next/static ./static/_next/static/
# y serviría otro servidor para páginas dinámicas.

# Crear fallback index.html solo si el build no produjo uno
RUN [ -f /app/static/index.html ] || echo '<!DOCTYPE html><html><head><title>Sistema Educativo</title></head><body><h1>🎓 Sistema Educativo Multiagente</h1><p><a href="/docs">Ver API Documentation</a></p></body></html>' > /app/static/index.html

# Cambiar permisos al usuario app
RUN chown -R app:app /app

# Dejamos root para que Nginx pueda bindear al puerto 80 (simple). 
# (Mejora futura: usar setcap o puerto >1024 y volver a usuario app)
USER root

# Variables de entorno para la aplicación
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1
ENV RELOAD=false

# Exponer puerto HTTP servido por Nginx
EXPOSE 80

# Health check a través de Nginx (proxy a FastAPI)
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Archivo supervisor: ejecuta uvicorn en 8001 y nginx en 80
# Si no existe (fallback), lo generamos rápido
RUN grep -q '\[program:api\]' /etc/supervisor/conf.d/supervisord.conf || echo "[supervisord]\nnodaemon=true\n[program:api]\ncommand=python -m uvicorn src.main_simple:app --host 127.0.0.1 --port 8001 --workers 1\n[program:nginx]\ncommand=/usr/sbin/nginx -g 'daemon off;'" > /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord","-n"]

