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

# Build del frontend para producción
ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Backend Python con Frontend estático
FROM python:3.11-slim AS production

# Variables de sistema
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gcc \
    g++ \
    build-essential \
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

# Copiar sitio estático exportado (Next.js output export genera /frontend/out)
# y además conservar el código fuente del frontend dentro de /app/frontend-src (opcional para debug)
COPY --from=frontend-builder /frontend/out/ ./static/
COPY --from=frontend-builder /frontend/ ./frontend-src/

# (Opcional) Si se cambiara a modo no-export, se podría copiar sólo los assets:
# COPY --from=frontend-builder /frontend/.next/static ./static/_next/static/
# y serviría otro servidor para páginas dinámicas.

# Crear fallback index.html solo si el build no produjo uno
RUN [ -f /app/static/index.html ] || echo '<!DOCTYPE html><html><head><title>Sistema Educativo</title></head><body><h1>🎓 Sistema Educativo Multiagente</h1><p><a href="/docs">Ver API Documentation</a></p></body></html>' > /app/static/index.html

# Cambiar permisos al usuario app
RUN chown -R app:app /app

# Cambiar a usuario no-root
USER app

# Variables de entorno para la aplicación
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1
ENV RELOAD=false

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio usando main_simple.py
CMD ["python", "-m", "uvicorn", "src.main_simple:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

