#!/bin/bash

# Script para aplicar configuración de variables de entorno a Azure Container Apps
# Educational System Environment Configuration

set -e

# Colores
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

# Función para verificar login en Azure
check_azure_login() {
    if ! az account show &> /dev/null; then
        print_info "Iniciando sesión en Azure..."
        az login --output none
    fi
    
    # Mostrar cuenta actual
    echo -e "${BLUE}Cuenta actual:${NC}"
    az account show --query "{name:name, subscriptionId:id}" --output table
}

# Función para crear secrets en Azure Container Apps
create_secrets() {
    print_header "Creando secrets en Azure Container Apps"
    
    # Verificar si la aplicación existe
    if ! az containerapp show --name educational-api --resource-group $RESOURCE_GROUP &> /dev/null; then
        print_error "La aplicación educational-api no existe en el grupo $RESOURCE_GROUP"
        echo "Por favor, ejecuta el despliegue primero: ./deploy-azure-auto.sh"
        exit 1
    fi
    
    print_info "Creando secrets para la aplicación..."
    
    # Crear los secrets
    az containerapp secret set \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --secrets \
            postgres-password=$POSTGRES_PASSWORD \
            redis-password=$REDIS_PASSWORD \
            rabbitmq-password=$RABBITMQ_PASSWORD \
            groq-api-key=$GROQ_API_KEY \
            openai-api-key=$OPENAI_API_KEY \
            jwt-secret=$JWT_SECRET \
            secret-key=$SECRET_KEY
    
    print_success "Secrets creados exitosamente"
}

# Función para actualizar la aplicación con las nuevas variables
update_app_with_secrets() {
    print_header "Actualizando aplicación con variables de entorno"
    
    # Obtener las URLs de los servicios
    POSTGRES_FQDN=$(az containerapp show --name educational-postgres --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv 2>/dev/null || echo "educational-postgres")
    REDIS_FQDN=$(az containerapp show --name educational-redis --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv 2>/dev/null || echo "educational-redis")
    RABBITMQ_FQDN=$(az containerapp show --name educational-rabbitmq --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv 2>/dev/null || echo "educational-rabbitmq")
    
    # Actualizar la aplicación con las variables de entorno usando secrets
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --set-env-vars \
            ENVIRONMENT=production \
            WORKERS=4 \
            UVICORN_HOST=0.0.0.0 \
            UVICORN_PORT=8000 \
            LOG_LEVEL=INFO \
            POSTGRES_DB=$POSTGRES_DB \
            POSTGRES_USER=$POSTGRES_USER \
            POSTGRES_HOST=$POSTGRES_HOST \
            POSTGRES_PORT=$POSTGRES_PORT \
            REDIS_HOST=$REDIS_HOST \
            REDIS_PORT=$REDIS_PORT \
            RABBITMQ_USER=$RABBITMQ_USER \
            RABBITMQ_HOST=$RABBITMQ_HOST \
            RABBITMQ_PORT=$RABBITMQ_PORT \
            DATABASE_URL="secretref:database-url" \
            REDIS_URL="secretref:redis-url" \
            RABBITMQ_URL="secretref:rabbitmq-url" \
            GROQ_API_KEY="secretref:groq-api-key" \
            OPENAI_API_KEY="secretref:openai-api-key" \
            SECRET_KEY="secretref:secret-key" \
            JWT_SECRET="secretref:jwt-secret"
    
    print_success "Aplicación actualizada con variables de entorno"
}

# Función para crear una configuración completa con todas las URLs
create_full_configuration() {
    print_header "Creando configuración completa"
    
    # Generar las URLs completas usando los secrets
    DATABASE_URL="postgresql://$POSTGRES_USER:secretref:postgres-password@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
    REDIS_URL="redis://default:secretref:redis-password@$REDIS_HOST:$REDIS_PORT/0"
    RABBITMQ_URL="amqp://$RABBITMQ_USER:secretref:rabbitmq-password@$RABBITMQ_HOST:$RABBITMQ_PORT/"
    
    # Actualizar la aplicación con todas las variables
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --set-env-vars \
            ENVIRONMENT=$ENVIRONMENT \
            WORKERS=$WORKERS \
            UVICORN_HOST=$UVICORN_HOST \
            UVICORN_PORT=$UVICORN_PORT \
            LOG_LEVEL=$LOG_LEVEL \
            POSTGRES_DB=$POSTGRES_DB \
            POSTGRES_USER=$POSTGRES_USER \
            POSTGRES_HOST=$POSTGRES_HOST \
            POSTGRES_PORT=$POSTGRES_PORT \
            REDIS_HOST=$REDIS_HOST \
            REDIS_PORT=$REDIS_PORT \
            RABBITMQ_USER=$RABBITMQ_USER \
            RABBITMQ_HOST=$RABBITMQ_HOST \
            RABBITMQ_PORT=$RABBITMQ_PORT \
            DATABASE_URL="secretref:database-url" \
            REDIS_URL="secretref:redis-url" \
            RABBITMQ_URL="secretref:rabbitmq-url" \
            GROQ_API_KEY="secretref:groq-api-key" \
            OPENAI_API_KEY="secretref:openai-api-key" \
            SECRET_KEY="secretref:secret-key" \
            JWT_SECRET="secretref:jwt-secret" \
            UPLOAD_DIR=$UPLOAD_DIR \
            MAX_FILE_SIZE=$MAX_FILE_SIZE \
            ALLOWED_EXTENSIONS=$ALLOWED_EXTENSIONS
    
    # También crear las URLs como secrets
    az containerapp secret set \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --secrets \
            database-url=$DATABASE_URL \
            redis-url=$REDIS_URL \
            rabbitmq-url=$RABBITMQ_URL
    
    print_success "Configuración completa aplicada"
}

# Función para verificar el estado
check_status() {
    print_header "Verificando estado de la aplicación"
    
    # Obtener información de la aplicación
    APP_URL=$(az containerapp show \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    echo -e "${BLUE}URL de la aplicación:${NC} https://$APP_URL"
    echo -e "${BLUE}Health Check:${NC} https://$APP_URL/health"
    echo -e "${BLUE}Documentación:${NC} https://$APP_URL/docs"
    
    # Verificar si la aplicación está respondiendo
    if curl -f -s "https://$APP_URL/health" > /dev/null 2>&1; then
        print_success "La aplicación está respondiendo correctamente"
    else
        print_warning "La aplicación puede estar iniciando..."
        echo "Puedes verificar los logs con: az containerapp logs show --name educational-api --resource-group $RESOURCE_GROUP --follow"
    fi
}

# Función principal
main() {
    print_header "Aplicando configuración de variables de entorno"
    echo ""
    echo "Este script aplicará todas las variables de entorno configuradas"
    echo "en el archivo .env.azure a tu despliegue de Azure Container Apps"
    echo ""
    
    read -p "¿Desea continuar? (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Operación cancelada"
        exit 1
    fi
    
    load_environment
    check_azure_login
    create_secrets
    create_full_configuration
    check_status
    
    print_header "✅ Configuración aplicada exitosamente!"
    echo ""
    echo "Tu aplicación ahora está configurada con todas las variables de entorno"
    echo "y está lista para ser usada en producción."
    echo ""
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi