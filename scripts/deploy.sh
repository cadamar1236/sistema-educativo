#!/bin/bash

# Script de despliegue para producción
# Este script automatiza el despliegue de la aplicación educativa

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
ENVIRONMENT=${ENVIRONMENT:-production}
DOMAIN=${DOMAIN:-localhost}
SSL_EMAIL=${SSL_EMAIL:-admin@localhost.com}
DEPLOYMENT_DIR=${DEPLOYMENT_DIR:-/opt/educational-system}

# Funciones auxiliares
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Verificar requisitos
verify_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado. Por favor instala Docker primero."
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
    fi
    
    # Verificar memoria mínima
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 4 ]; then
        warning "La memoria recomendada es de al menos 4GB. Memoria actual: ${MEMORY_GB}GB"
    fi
    
    log "Requisitos verificados correctamente"
}

# Configurar variables de entorno
setup_environment() {
    log "Configurando variables de entorno..."
    
    # Crear archivo .env si no existe
    if [ ! -f .env ]; then
        cat > .env << EOF
# Configuración de base de datos
POSTGRES_PASSWORD=secure_password_$(openssl rand -hex 16)
POSTGRES_REPLICA_PASSWORD=replica_password_$(openssl rand -hex 16)

# Configuración de Redis
REDIS_PASSWORD=redis_password_$(openssl rand -hex 16)

# Configuración de RabbitMQ
RABBITMQ_PASSWORD=rabbit_password_$(openssl rand -hex 16)

# Configuración de Grafana
GRAFANA_PASSWORD=grafana_password_$(openssl rand -hex 16)

# Configuración de aplicación
ENVIRONMENT=production
DEBUG=false
WORKERS=4

# Configuración de dominio
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL

# Variables de API
GROQ_API_KEY=your_groq_api_key_here

# Configuración de monitoreo
MONITORING_ENABLED=true
ALERTING_ENABLED=true
BACKUP_ENABLED=true
EOF
        log "Archivo .env creado con configuraciones por defecto"
        info "Por favor edita el archivo .env con tus configuraciones específicas"
    else
        log "Archivo .env ya existe, usando configuraciones existentes"
    fi
}

# Configurar SSL
setup_ssl() {
    log "Configurando certificados SSL..."
    
    mkdir -p ssl
    
    if [ "$ENVIRONMENT" = "production" ]; then
        info "Configurando SSL con Let's Encrypt para producción..."
        
        # Instalar certbot si no está disponible
        if ! command -v certbot &> /dev/null; then
            info "Instalando certbot..."
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y certbot
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot
            fi
        fi
        
        # Generar certificado SSL
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            info "Certificado SSL ya existe, copiando..."
            cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
            cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem
        else
            info "Generando certificado SSL auto-firmado para desarrollo..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/key.pem -out ssl/cert.pem \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        fi
    else
        info "Generando certificado SSL auto-firmado para desarrollo..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem -out ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    fi
    
    chmod 600 ssl/key.pem ssl/cert.pem
    log "Certificados SSL configurados"
}

# Construir imágenes Docker
build_images() {
    log "Construyendo imágenes Docker..."
    
    # Limpiar imágenes antiguas
    docker system prune -f
    
    # Construir imágenes
    docker-compose -f docker-compose.production.yml build --no-cache
    
    log "Imágenes Docker construidas exitosamente"
}

# Inicializar base de datos
initialize_database() {
    log "Inicializando base de datos..."
    
    # Iniciar solo servicios de base de datos
    docker-compose -f docker-compose.production.yml up -d postgres-primary postgres-replica redis-master
    
    # Esperar a que los servicios estén listos
    info "Esperando a que los servicios de base de datos estén listos..."
    sleep 30
    
    # Verificar conexiones
    docker-compose -f docker-compose.production.yml exec -T postgres-primary \
        psql -U admin -d educational_system -c "SELECT 1;"
    
    log "Base de datos inicializada"
}

# Desplegar aplicación
deploy_application() {
    log "Desplegando aplicación..."
    
    # Detener servicios existentes
    docker-compose -f docker-compose.production.yml down
    
    # Iniciar todos los servicios
    docker-compose -f docker-compose.production.yml up -d
    
    # Esperar a que todos los servicios estén listos
    info "Esperando a que todos los servicios estén listos..."
    sleep 60
    
    # Verificar estado de los servicios
    docker-compose -f docker-compose.production.yml ps
    
    log "Aplicación desplegada exitosamente"
}

# Configurar monitoreo
setup_monitoring() {
    log "Configurando monitoreo..."
    
    # Esperar a que los servicios de monitoreo estén listos
    sleep 30
    
    # Configurar Grafana
    curl -X POST \
        http://admin:${GRAFANA_PASSWORD:-grafana_password_2024}@localhost:3000/api/datasources \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "access": "proxy",
            "isDefault": true
        }' || true
    
    log "Monitoreo configurado"
}

# Verificar salud del sistema
health_check() {
    log "Realizando verificación de salud..."
    
    # Verificar API principal
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "API principal: HEALTHY"
    else
        error "API principal: UNHEALTHY"
    fi
    
    # Verificar PostgreSQL
    if docker-compose -f docker-compose.production.yml exec -T postgres-primary \
        pg_isready -U admin -d educational_system; then
        log "PostgreSQL: HEALTHY"
    else
        error "PostgreSQL: UNHEALTHY"
    fi
    
    # Verificar Redis
    if docker-compose -f docker-compose.production.yml exec -T redis-master \
        redis-cli ping | grep -q "PONG"; then
        log "Redis: HEALTHY"
    else
        error "Redis: UNHEALTHY"
    fi
    
    # Verificar RabbitMQ
    if curl -f http://localhost:15672/api/healthchecks/node \
        -u admin:${RABBITMQ_PASSWORD:-rabbit_password_2024} > /dev/null 2>&1; then
        log "RabbitMQ: HEALTHY"
    else
        error "RabbitMQ: UNHEALTHY"
    fi
    
    log "Verificación de salud completada"
}

# Configurar backup automático
setup_backup() {
    log "Configurando backup automático..."
    
    # Crear script de backup
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
# Script de backup para la base de datos

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backups
mkdir -p $BACKUP_DIR

# Backup de base de datos
docker-compose -f docker-compose.production.yml exec -T postgres-primary \
    pg_dump -U admin educational_system | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Backup de configuración
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz config/

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
EOF
    
    chmod +x scripts/backup.sh
    
    # Configurar cron job (si está disponible)
    if command -v crontab > /dev/null 2>&1; then
        (crontab -l 2>/dev/null || echo "") | cat - << EOF
# Backup diario a las 2 AM
0 2 * * * /opt/educational-system/scripts/backup.sh >> /var/log/backup.log 2>&1
EOF
        log "Backup automático configurado"
    fi
}

# Mostrar información de acceso
show_access_info() {
    log "=== INFORMACIÓN DE ACCESO ==="
    echo ""
    echo "Aplicación principal: http://$DOMAIN"
    echo "API Health Check: http://$DOMAIN/health"
    echo "Grafana: http://$DOMAIN:3000 (admin/${GRAFANA_PASSWORD:-grafana_password_2024})"
    echo "Prometheus: http://$DOMAIN:9090"
    echo "RabbitMQ: http://$DOMAIN:15672 (admin/${RABBITMQ_PASSWORD:-rabbit_password_2024})"
    echo "Kibana: http://$DOMAIN:5601"
    echo ""
    echo "=== COMANDOS ÚTILES ==="
    echo "Ver logs: docker-compose -f docker-compose.production.yml logs -f"
    echo "Reiniciar servicio: docker-compose -f docker-compose.production.yml restart api"
    echo "Escalar servicio: docker-compose -f docker-compose.production.yml up --scale api=3"
    echo "Actualizar: ./deploy.sh --update"
    echo ""
}

# Actualizar aplicación
update_application() {
    log "Actualizando aplicación..."
    
    # Obtener últimos cambios
    git pull origin main
    
    # Reconstruir imágenes
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Actualizar servicios
    docker-compose -f docker-compose.production.yml up -d
    
    log "Aplicación actualizada exitosamente"
}

# Función principal
main() {
    case "${1:-deploy}" in
        "deploy")
            verify_requirements
            setup_environment
            setup_ssl
            build_images
            initialize_database
            deploy_application
            setup_monitoring
            setup_backup
            health_check
            show_access_info
            ;;
        "update")
            update_application
            ;;
        "health")
            health_check
            ;;
        "backup")
            setup_backup
            ;;
        "logs")
            docker-compose -f docker-compose.production.yml logs -f
            ;;
        *)
            echo "Uso: $0 {deploy|update|health|backup|logs}"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"