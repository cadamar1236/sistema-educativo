#!/bin/bash

# Azure Container Apps Quick Deployment Script
# Educational System - Production Deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration - MODIFICA ESTOS VALORES
RESOURCE_GROUP="educational-system-rg"
LOCATION="eastus"
CONTAINERAPPS_ENVIRONMENT="educational-env"
REGISTRY_NAME="educationalacr$(date +%s)"  # Nombre único
API_APP_NAME="educational-api"

# Función para verificar herramientas
check_tools() {
    print_header "Verificando herramientas necesarias"
    
    # Verificar Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI no está instalado. Instálalo con:"
        echo "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        exit 1
    fi
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado. Instálalo desde: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    print_success "Todas las herramientas están disponibles"
}

# Login a Azure
azure_login() {
    print_header "Iniciando sesión en Azure"
    az login --output none
    
    # Mostrar cuenta actual
    echo "Cuenta actual:"
    az account show --query "{name:name, id:id}" --output table
    
    read -p "¿Es esta la suscripción correcta? (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Por favor, cambia de suscripción con: az account set --subscription <ID>"
        exit 1
    fi
}

# Crear recursos base
create_base_resources() {
    print_header "Creando recursos base"
    
    # Crear grupo de recursos
    print_info "Creando grupo de recursos..."
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    print_success "Grupo de recursos creado: $RESOURCE_GROUP"
    
    # Crear Container Registry
    print_info "Creando Container Registry..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $REGISTRY_NAME \
        --sku Basic \
        --admin-enabled true \
        --output none
    print_success "Container Registry creado: $REGISTRY_NAME.azurecr.io"
    
    # Login al registry
    az acr login --name $REGISTRY_NAME --output none
}

# Build y push de imagen
build_and_push() {
    print_header "Construyendo y subiendo imagen Docker"
    
    # Build
    print_info "Construyendo imagen..."
    docker build -t educational-app:latest .
    
    # Tag
    docker tag educational-app:latest $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    # Push
    print_info "Subiendo imagen a Azure Container Registry..."
    docker push $REGISTRY_NAME.azurecr.io/educational-app:latest
    print_success "Imagen subida exitosamente"
}

# Desplegar aplicación
deploy_application() {
    print_header "Desplegando aplicación en Azure Container Apps"
    
    # Crear ambiente
    print_info "Creando ambiente de Container Apps..."
    az containerapp env create \
        --name $CONTAINERAPPS_ENVIRONMENT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    
    # Desplegar aplicación
    print_info "Desplegando aplicación..."
    az containerapp create \
        --name $API_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image $REGISTRY_NAME.azurecr.io/educational-app:latest \
        --cpu 1.0 \
        --memory 2Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --env-vars \
            ENVIRONMENT=production \
            WORKERS=2 \
            UVICORN_WORKERS=2 \
            UVICORN_HOST=0.0.0.0 \
            UVICORN_PORT=8000 \
        --ingress external \
        --target-port 8000 \
        --transport http \
        --registry-server $REGISTRY_NAME.azurecr.io \
        --registry-username $REGISTRY_NAME \
        --registry-password $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv) \
        --output none
    
    # Obtener URL
    APP_URL=$(az containerapp show \
        --name $API_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    print_success "Aplicación desplegada exitosamente!"
    echo ""
    echo -e "${GREEN}URL de la aplicación: https://$APP_URL${NC}"
    echo ""
    echo "Endpoints disponibles:"
    echo "  - Health Check: https://$APP_URL/health"
    echo "  - Documentación: https://$APP_URL/docs"
    echo "  - Redoc: https://$APP_URL/redoc"
}

# Configuración de autoescalado
configure_scaling() {
    print_header "Configurando autoescalado"
    
    az containerapp update \
        --name $API_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name cpu-scaling \
        --scale-rule-type cpu \
        --scale-rule-metadata "metricType=Utilization" "metricValue=70" \
        --scale-rule-auth \
        --output none
    
    print_success "Autoescalado configurado"
}

# Función principal
main() {
    print_header "Despliegue de Educational System en Azure Container Apps"
    echo ""
    echo "Configuración:"
    echo "  - Grupo de recursos: $RESOURCE_GROUP"
    echo "  - Ubicación: $LOCATION"
    echo "  - Container Registry: $REGISTRY_NAME.azurecr.io"
    echo "  - Container App: $API_APP_NAME"
    echo ""
    
    # Verificar pasos
    read -p "¿Desea continuar con el despliegue? (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Despliegue cancelado"
        exit 1
    fi
    
    check_tools
    azure_login
    create_base_resources
    build_and_push
    deploy_application
    configure_scaling
    
    print_header "Despliegue completado exitosamente!"
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi