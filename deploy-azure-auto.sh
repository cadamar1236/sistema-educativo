#!/bin/bash

# Azure Container Apps - Despliegue Automático con Variables de Entorno
# Educational System - Production Deployment

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Función para cargar variables de entorno
load_environment() {
    if [ -f .env.azure ]; then
        print_info "Cargando variables de entorno de .env.azure"
        export $(cat .env.azure | xargs)
        print_success "Variables de entorno cargadas"
    else
        print_error "Archivo .env.azure no encontrado"
        print_info "Ejecuta ./configure-azure-env.sh primero para crear la configuración"
        exit 1
    fi
}

# Función para verificar herramientas
check_tools() {
    print_header "Verificando herramientas"
    
    # Verificar Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI no está instalado"
        echo "Instálalo con: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        exit 1
    fi
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        echo "Instálalo desde: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Verificar que estemos logueados en Azure
    if ! az account show &> /dev/null; then
        print_info "Iniciando sesión en Azure..."
        az login --output none
    fi
    
    print_success "Todas las herramientas están disponibles"
}

# Función para crear recursos de Azure
create_azure_resources() {
    print_header "Creando recursos de Azure"
    
    # Crear grupo de recursos
    print_info "Creando grupo de recursos: $RESOURCE_GROUP"
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    print_success "Grupo de recursos creado"
    
    # Crear Container Registry
    print_info "Creando Container Registry: $REGISTRY_NAME"
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true --output none
    print_success "Container Registry creado"
    
    # Login al registry
    az acr login --name $REGISTRY_NAME --output none
    print_success "Login al Container Registry exitoso"
}

# Función para build y push de imagen
build_and_push_image() {
    print_header "Build y Push de la imagen Docker"
    
    # Build de la imagen
    print_info "Construyendo la imagen Docker..."
    docker build -t educational-app:latest .
    
    # Tag de la imagen
    docker tag educational-app:latest $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    # Push al registry
    print_info "Subiendo la imagen a Azure Container Registry..."
    docker push $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    print_success "Imagen subida exitosamente"
}

# Función para crear entorno de Container Apps
create_container_apps_environment() {
    print_header "Creando entorno de Container Apps"
    
    az containerapp env create \
        --name $CONTAINERAPPS_ENVIRONMENT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    
    print_success "Entorno de Container Apps creado"
}

# Función para desplegar PostgreSQL
deploy_postgresql() {
    print_header "Desplegando PostgreSQL"
    
    az containerapp create \
        --name educational-postgres \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image postgres:15-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            POSTGRES_DB=$POSTGRES_DB \
            POSTGRES_USER=$POSTGRES_USER \
            POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
            POSTGRES_REPLICA_USER=replica \
            POSTGRES_REPLICA_PASSWORD=$POSTGRES_PASSWORD \
        --ingress internal \
        --target-port 5432 \
        --transport tcp \
        --output none
    
    print_success "PostgreSQL desplegado"
}

# Función para desplegar Redis
deploy_redis() {
    print_header "Desplegando Redis"
    
    az containerapp create \
        --name educational-redis \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image redis:7-alpine \
        --cpu 0.25 --memory 0.5Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars REDIS_PASSWORD=$REDIS_PASSWORD \
        --ingress internal \
        --target-port 6379 \
        --transport tcp \
        --output none
    
    print_success "Redis desplegado"
}

# Función para desplegar RabbitMQ
deploy_rabbitmq() {
    print_header "Desplegando RabbitMQ"
    
    az containerapp create \
        --name educational-rabbitmq \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image rabbitmq:3-management-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            RABBITMQ_DEFAULT_USER=$RABBITMQ_USER \
            RABBITMQ_DEFAULT_PASS=$RABBITMQ_PASSWORD \
        --ingress internal \
        --target-port 5672 \
        --transport tcp \
        --output none
    
    print_success "RabbitMQ desplegado"
}

# Función para desplegar la aplicación principal
deploy_main_app() {
    print_header "Desplegando aplicación principal"
    
    # Esperar a que los servicios estén listos
    print_info "Esperando a que los servicios estén listos..."
    sleep 30
    
    # Desplegar la aplicación
    az containerapp create \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image $REGISTRY_NAME.azurecr.io/educational-app:latest \
        --cpu 1.0 --memory 2Gi \
        --min-replicas 2 --max-replicas 10 \
        --env-vars \
            DATABASE_URL=$DATABASE_URL \
            REDIS_URL=$REDIS_URL \
            RABBITMQ_URL=$RABBITMQ_URL \
            ENVIRONMENT=$ENVIRONMENT \
            WORKERS=$WORKERS \
            GROQ_API_KEY=$GROQ_API_KEY \
            OPENAI_API_KEY=$OPENAI_API_KEY \
            SECRET_KEY=$SECRET_KEY \
            LOG_LEVEL=$LOG_LEVEL \
        --ingress external \
        --target-port 8000 \
        --transport http \
        --registry-server $REGISTRY_NAME.azurecr.io \
        --registry-username $REGISTRY_NAME \
        --registry-password $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv) \
        --output none
    
    print_success "Aplicación principal desplegada"
}

# Función para configurar auto-scaling
configure_scaling() {
    print_header "Configurando auto-scaling"
    
    # Configurar regla de escalado basada en CPU
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name cpu-scaling \
        --scale-rule-type cpu \
        --scale-rule-metadata "metricType=Utilization" "metricValue=70" \
        --scale-rule-auth \
        --output none
    
    # Configurar regla de escalado basada en memoria
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name memory-scaling \
        --scale-rule-type memory \
        --scale-rule-metadata "metricType=Utilization" "metricValue=80" \
        --scale-rule-auth \
        --output none
    
    print_success "Auto-scaling configurado"
}

# Función para obtener información de la aplicación
get_app_info() {
    print_header "Información de la aplicación"
    
    # Obtener URL de la aplicación
    APP_URL=$(az containerapp show \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    echo -e "${GREEN}✓ Despliegue completado exitosamente!${NC}"
    echo ""
    echo -e "${BLUE}URL de la aplicación:${NC} https://$APP_URL"
    echo -e "${BLUE}Health Check:${NC} https://$APP_URL/health"
    echo -e "${BLUE}Documentación API:${NC} https://$APP_URL/docs"
    echo -e "${BLUE}Redoc:${NC} https://$APP_URL/redoc"
    echo ""
    echo -e "${BLUE}Recursos creados:${NC}"
    echo "  - Grupo de recursos: $RESOURCE_GROUP"
    echo "  - Container Registry: $REGISTRY_NAME.azurecr.io"
    echo "  - Container Apps Environment: $CONTAINERAPPS_ENVIRONMENT"
    echo ""
    echo -e "${BLUE}Servicios desplegados:${NC}"
    echo "  - educational-api (aplicación principal)"
    echo "  - educational-postgres (base de datos)"
    echo "  - educational-redis (caché)"
    echo "  - educational-rabbitmq (cola de mensajes)"
    echo ""
    
    # Guardar información en un archivo
    cat > deployment-info.txt << EOF
Despliegue completado: $(date)
URL de la aplicación: https://$APP_URL
Grupo de recursos: $RESOURCE_GROUP
Registry: $REGISTRY_NAME.azurecr.io

Comandos útiles:
- Ver logs: az containerapp logs show --name educational-api --resource-group $RESOURCE_GROUP --follow
- Escalar: az containerapp update --name educational-api --resource-group $RESOURCE_GROUP --min-replicas 5
- Monitorear: az monitor metrics list --resource educational-api --resource-group $RESOURCE_GROUP --resource-type Microsoft.App/containerApps
EOF
    
    print_success "Información guardada en deployment-info.txt"
}

# Función principal de despliegue
main() {
    print_header "Despliegue Automático de Educational System en Azure Container Apps"
    echo ""
    echo "Este script desplegará tu sistema educativo completo en Azure Container Apps"
    echo "con todas las variables de entorno configuradas automáticamente."
    echo ""
    
    # Verificar si desea continuar
    read -p "¿Desea continuar con el despliegue? (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Despliegue cancelado"
        exit 1
    fi
    
    # Ejecutar pasos del despliegue
    load_environment
    check_tools
    create_azure_resources
    build_and_push_image
    create_container_apps_environment
    deploy_postgresql
    deploy_redis
    deploy_rabbitmq
    deploy_main_app
    configure_scaling
    get_app_info
    
    print_header "🎉 Despliegue completado exitosamente!"
    echo "Tu aplicación está ahora disponible en Azure Container Apps"
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi