#!/bin/bash

# Azure Container Apps - Full Stack Deployment
# Educational System con PostgreSQL, Redis y RabbitMQ

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Configuración
RESOURCE_GROUP="educational-system-rg"
LOCATION="eastus"
ENVIRONMENT="educational-env"
REGISTRY_NAME="educationalacr$(date +%s)"

# Variables de entorno (¡CAMBIA ESTOS VALORES!)
POSTGRES_PASSWORD="$(openssl rand -base64 32)"
REDIS_PASSWORD="$(openssl rand -base64 32)"
RABBITMQ_PASSWORD="$(openssl rand -base64 32)"

# Función de despliegue
main() {
    print_header "Despliegue completo de Educational System"
    
    # 1. Login y preparación
    az login --output none
    
    # 2. Crear grupo de recursos
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    
    # 3. Crear Container Registry
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true --output none
    az acr login --name $REGISTRY_NAME --output none
    
    # 4. Build y push de imagen
    docker build -t educational-app:latest .
    docker tag educational-app:latest $REGISTRY_NAME.azurecr.io/educational-app:latest
    docker push $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    # 5. Crear Container Apps Environment
    az containerapp env create --name $ENVIRONMENT --resource-group $RESOURCE_GROUP --location $LOCATION --output none
    
    # 6. Desplegar PostgreSQL
    az containerapp create \
        --name educational-postgres \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT \
        --image postgres:15-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars POSTGRES_DB=educational_system POSTGRES_USER=admin POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
        --ingress internal --target-port 5432 --transport tcp --output none
    
    # 7. Desplegar Redis
    az containerapp create \
        --name educational-redis \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT \
        --image redis:7-alpine \
        --cpu 0.25 --memory 0.5Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars REDIS_PASSWORD=$REDIS_PASSWORD \
        --ingress internal --target-port 6379 --transport tcp --output none
    
    # 8. Desplegar RabbitMQ
    az containerapp create \
        --name educational-rabbitmq \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT \
        --image rabbitmq:3-management-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars RABBITMQ_DEFAULT_USER=admin RABBITMQ_DEFAULT_PASS=$RABBITMQ_PASSWORD \
        --ingress internal --target-port 5672 --transport tcp --output none
    
    # 9. Esperar a que los servicios estén listos
    echo "Esperando que los servicios estén listos..."
    sleep 60
    
    # 10. Desplegar aplicación principal
    az containerapp create \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT \
        --image $REGISTRY_NAME.azurecr.io/educational-app:latest \
        --cpu 1.0 --memory 2Gi \
        --min-replicas 1 --max-replicas 3 \
        --env-vars \
            DATABASE_URL="postgresql://admin:$POSTGRES_PASSWORD@educational-postgres:5432/educational_system" \
            REDIS_URL="redis://default:$REDIS_PASSWORD@educational-redis:6379/0" \
            RABBITMQ_URL="amqp://admin:$RABBITMQ_PASSWORD@educational-rabbitmq:5672/" \
            ENVIRONMENT=production \
            WORKERS=2 \
            UVICORN_WORKERS=2 \
            UVICORN_HOST=0.0.0.0 \
            UVICORN_PORT=8000 \
        --ingress external --target-port 8000 --transport http \
        --registry-server $REGISTRY_NAME.azurecr.io \
        --registry-username $REGISTRY_NAME \
        --registry-password $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv) \
        --output none
    
    # 11. Obtener URL
    APP_URL=$(az containerapp show --name educational-api --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)
    
    print_header "Despliegue completado!"
    echo ""
    echo -e "${GREEN}URL de la aplicación: https://$APP_URL${NC}"
    echo ""
    echo "Credenciales de administrador:"
    echo "  - PostgreSQL Password: $POSTGRES_PASSWORD"
    echo "  - Redis Password: $REDIS_PASSWORD"
    echo "  - RabbitMQ Password: $RABBITMQ_PASSWORD"
}

# Ejecutar
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    read -p "¿Desea continuar con el despliegue? Esto puede tardar varios minutos (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Despliegue cancelado"
        exit 1
    fi
    
    main
fi