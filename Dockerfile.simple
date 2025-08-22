# Dockerfile específico para main_simple.py con fullstack
FROM node:18-slim as frontend-builder

WORKDIR /app

# Copiar archivos del frontend
COPY julia-frontend/package*.json ./
RUN npm install

# Copiar código fuente del frontend
COPY julia-frontend/ ./

# Construir frontend para producción
RUN npm run build

# Stage final - Backend Python
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /app/data/uploads /app/data/temp /app/logs /app/static && \
    chown -R app:app /app

# Copiar código de la aplicación
COPY . .

# Copiar frontend build desde el stage anterior
COPY --from=frontend-builder /app/.next/standalone ./static/
COPY --from=frontend-builder /app/.next/static ./static/_next/static/
COPY --from=frontend-builder /app/public ./static/public/

# Cambiar permisos
RUN chown -R app:app /app

# Cambiar a usuario no-root
USER app

# Variables de entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio - usando main_simple
CMD ["python", "-m", "uvicorn", "src.main_simple:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
