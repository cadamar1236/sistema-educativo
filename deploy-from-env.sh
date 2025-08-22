#!/bin/bash

# Azure Container Apps Deployment - Lee variables desde .env existente
# Educational System - Production Deployment

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

# Función para leer variables del .env existente
load_env_from_dotenv() {
    if [ -f .env ]; then
        print_info "Leyendo variables de entorno de .env"
        
        # Leer variables del .env y exportarlas
        set -a
        source .env
        set +a
        
        # Configurar variables predeterminadas si no están en .env
        : ${RESOURCE_GROUP:=educational-system-rg}
        : ${LOCATION:=eastus}
        : ${CONTAINERAPPS_ENVIRONMENT:=educational-env}
        : ${REGISTRY_NAME:=educationalacr}
        : ${ENVIRONMENT:=production}
        : ${WORKERS:=4}
        : ${UVICORN_HOST:=0.0.0.0}
        : ${UVICORN_PORT:=8000}
        : ${POSTGRES_DB:=educational_system}
        : ${POSTGRES_USER:=admin}
        : ${POSTGRES_HOST:=educational-postgres}
        : ${POSTGRES_PORT:=5432}
        : ${REDIS_HOST:=educational-redis}
        : ${REDIS_PORT:=6379}
        : ${RABBITMQ_USER:=admin}
        : ${RABBITMQ_HOST:=educational-rabbitmq}
        : ${RABBITMQ_PORT:=5672}
        : ${LOG_LEVEL:=INFO}
        : ${UPLOAD_DIR:=/app/uploads}
        : ${MAX_FILE_SIZE:=10485760}
        : ${ALLOWED_EXTENSIONS:=pdf,doc,docx,txt,md}
        
        # Generar DATABASE_URL si no existe
        if [ -z "$DATABASE_URL" ]; then
            DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
        fi
        
        # Generar REDIS_URL si no existe
        if [ -z "$REDIS_URL" ]; then
            REDIS_URL="redis://default:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/0"
        fi
        
        # Generar RABBITMQ_URL si no existe
        if [ -z "$RABBITMQ_URL" ]; then
            RABBITMQ_URL="amqp://$RABBITMQ_USER:$RABBITMQ_PASSWORD@$RABBITMQ_HOST:$RABBITMQ_PORT/"
        fi
        
        print_success "Variables de entorno cargadas desde .env"
    else
        print_error "Archivo .env no encontrado"
        echo "Por favor, asegúrate de tener un archivo .env en el directorio actual"
        exit 1
    fi
}

# Función para verificar herramientas
check_tools() {
    print_header "Verificando herramientas"
    
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI no está instalado"
        echo "Instálalo con: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        echo "Instálalo desde: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        print_info "Iniciando sesión en Azure..."
        az login --output none
    fi
    
    print_success "Todas las herramientas están disponibles"
}

# Función para mostrar variables detectadas
show_detected_variables() {
    print_header "Variables detectadas en .env"
    
    # Mostrar variables principales (sin mostrar contraseñas)
    echo -e "${BLUE}Azure Configuration:${NC}"
    echo "  RESOURCE_GROUP: $RESOURCE_GROUP"
    echo "  LOCATION: $LOCATION"
    echo "  CONTAINERAPPS_ENVIRONMENT: $CONTAINERAPPS_ENVIRONMENT"
    echo "  REGISTRY_NAME: $REGISTRY_NAME"
    
    echo -e "\n${BLUE}Application Configuration:${NC}"
    echo "  ENVIRONMENT: $ENVIRONMENT"
    echo "  WORKERS: $WORKERS"
    echo "  UVICORN_HOST: $UVICORN_HOST"
    echo "  UVICORN_PORT: $UVICORN_PORT"
    
    echo -e "\n${BLUE}Database Configuration:${NC}"
    echo "  POSTGRES_DB: $POSTGRES_DB"
    echo "  POSTGRES_USER: $POSTGRES_USER"
    echo "  POSTGRES_HOST: $POSTGRES_HOST"
    echo "  POSTGRES_PORT: $POSTGRES_PORT"
    
    echo -e "\n${BLUE}API Keys:${NC}"
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "  OPENAI_API_KEY: ✓ Detectado"
    else
        echo "  OPENAI_API_KEY: ✗ No encontrado"
    fi
    
    if [ -n "$GROQ_API_KEY" ]; then
        echo "  GROQ_API_KEY: ✓ Detectado"
    else
        echo "  GROQ_API_KEY: ✗ No encontrado"
    fi
    
    echo -e "\n${YELLOW}Presiona Enter para continuar con el despliegue...${NC}"
    read
}

# Función para crear recursos de Azure
create_azure_resources() {
    print_header "Creando recursos de Azure"
    
    print_info "Creando grupo de recursos: $RESOURCE_GROUP"
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    
    print_info "Creando Container Registry: $REGISTRY_NAME"
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true --output none
    
    az acr login --name $REGISTRY_NAME --output none
    print_success "Recursos de Azure creados"
}

# Función para build y push
deploy_image() {
    print_header "Build y Push de imagen"
    
    print_info "Construyendo imagen Docker..."
    docker build -t educational-app:latest .
    
    docker tag educational-app:latest $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    print_info "Subiendo imagen a Azure Container Registry..."
    docker push $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    print_success "Imagen subida exitosamente"
}

# Función para crear entorno de Container Apps
create_environment() {
    print_header "Creando entorno de Container Apps"
    
    az containerapp env create \
        --name $CONTAINERAPPS_ENVIRONMENT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    
    print_success "Entorno creado"
}

# Función para desplegar servicios auxiliares
deploy_services() {
    print_header "Desplegando servicios auxiliares"
    
    # PostgreSQL
    print_info "Desplegando PostgreSQL..."
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
        --ingress internal \
        --target-port 5432 \
        --transport tcp \
        --output none
    
    # Redis
    print_info "Desplegando Redis..."
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
    
    # RabbitMQ
    print_info "Desplegando RabbitMQ..."
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
    
    print_success "Servicios auxiliares desplegados"
}

# Función para desplegar aplicación principal
deploy_app() {
    print_header "Desplegando aplicación principal"
    
    # Esperar a que los servicios estén listos
    print_info "Esperando a que los servicios estén listos..."
    sleep 20
    
    # Preparar variables para Azure
    AZURE_ENV_VARS=""
    AZURE_ENV_VARS+="ENVIRONMENT=$ENVIRONMENT "
    AZURE_ENV_VARS+="WORKERS=$WORKERS "
    AZURE_ENV_VARS+="UVICORN_HOST=$UVICORN_HOST "
    AZURE_ENV_VARS+="UVICORN_PORT=$UVICORN_PORT "
    AZURE_ENV_VARS+="LOG_LEVEL=$LOG_LEVEL "
    AZURE_ENV_VARS+="POSTGRES_DB=$POSTGRES_DB "
    AZURE_ENV_VARS+="POSTGRES_USER=$POSTGRES_USER "
    AZURE_ENV_VARS+="POSTGRES_HOST=$POSTGRES_HOST "
    AZURE_ENV_VARS+="POSTGRES_PORT=$POSTGRES_PORT "
    AZURE_ENV_VARS+="REDIS_HOST=$REDIS_HOST "
    AZURE_ENV_VARS+="REDIS_PORT=$REDIS_PORT "
    AZURE_ENV_VARS+="RABBITMQ_USER=$RABBITMQ_USER "
    AZURE_ENV_VARS+="RABBITMQ_HOST=$RABBITMQ_HOST "
    AZURE_ENV_VARS+="RABBITMQ_PORT=$RABBITMQ_PORT "
    AZURE_ENV_VARS+="DATABASE_URL=$DATABASE_URL "
    AZURE_ENV_VARS+="REDIS_URL=$REDIS_URL "
    AZURE_ENV_VARS+="RABBITMQ_URL=$RABBITMQ_URL "
    
    # Agregar variables opcionales si existen
    [ -n "$GROQ_API_KEY" ] && AZURE_ENV_VARS+="GROQ_API_KEY=$GROQ_API_KEY "
    [ -n "$OPENAI_API_KEY" ] && AZURE_ENV_VARS+="OPENAI_API_KEY=$OPENAI_API_KEY "
    [ -n "$ANTHROPIC_API_KEY" ] && AZURE_ENV_VARS+="ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY "
    [ -n "$SECRET_KEY" ] && AZURE_ENV_VARS+="SECRET_KEY=$SECRET_KEY "
    [ -n "$JWT_SECRET" ] && AZURE_ENV_VARS+="JWT_SECRET=$JWT_SECRET "
    [ -n "$UPLOAD_DIR" ] && AZURE_ENV_VARS+="UPLOAD_DIR=$UPLOAD_DIR "
    [ -n "$MAX_FILE_SIZE" ] && AZURE_ENV_VARS+="MAX_FILE_SIZE=$MAX_FILE_SIZE "
    [ -n "$ALLOWED_EXTENSIONS" ] && AZURE_ENV_VARS+="ALLOWED_EXTENSIONS=$ALLOWED_EXTENSIONS "
    
    # Desplegar la aplicación
    az containerapp create \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image $REGISTRY_NAME.azurecr.io/educational-app:latest \
        --cpu 1.0 --memory 2Gi \
        --min-replicas 2 --max-replicas 10 \
        --env-vars $AZURE_ENV_VARS \
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
    
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name cpu-scaling \
        --scale-rule-type cpu \
        --scale-rule-metadata "metricType=Utilization" "metricValue=70" \
        --scale-rule-auth \
        --output none
    
    print_success "Auto-scaling configurado"
}

# Función para obtener información final
get_app_info() {
    print_header "Información de la aplicación"
    
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
    
    # Guardar información
    cat > deployment-info.txt << EOF
Despliegue completado: $(date)
URL: https://$APP_URL
Variables leídas de: .env
Grupo de recursos: $RESOURCE_GROUP
Comandos útiles:
- Ver logs: az containerapp logs show --name educational-api --resource-group $RESOURCE_GROUP --follow
- Status: az containerapp show --name educational-api --resource-group $RESOURCE_GROUP
EOF
    
    print_success "Información guardada en deployment-info.txt"
}

# Función principal
main() {
    print_header "Despliegue de Educational System - Leyendo de .env"
    echo ""
    echo "Este script leerá las variables de entorno de tu archivo .env"
    echo "y desplegará tu aplicación completa a Azure Container Apps"
    echo ""
    
    read -p "¿Desea continuar con el despliegue? (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Despliegue cancelado"
        exit 1
    fi
    
    load_env_from_dotenv
    show_detected_variables
    check_tools
    
    # Preguntar confirmación final
    read -p "¿Confirmar despliegue con estas configuraciones? (s/n): " confirm_deploy
    if [[ $confirm_deploy != [sS] ]]; then
        echo "Despliegue cancelado"
        exit 1
    fi
    
    create_azure_resources
    deploy_image
    create_environment
    deploy_services
    deploy_app
    configure_scaling
    get_app_info
    
    print_header "🎉 Despliegue completado exitosamente!"
    echo "Tu aplicación está disponible en: https://$(az containerapp show --name educational-api --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)"
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi