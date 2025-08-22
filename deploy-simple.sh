#!/bin/bash

# Script simple para desplegar usando .env existente
# Lee directamente de tu archivo .env

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Desplegando desde .env${NC}"

# Cargar variables del .env
if [ -f .env ]; then
    echo -e "${YELLOW}📄 Cargando variables de .env...${NC}"
    set -a
    source .env
    set +a
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

# Configuración predeterminada si faltan valores
export RESOURCE_GROUP=${RESOURCE_GROUP:-educational-system-rg}
export LOCATION=${LOCATION:-eastus}
export CONTAINERAPPS_ENVIRONMENT=${CONTAINERAPPS_ENVIRONMENT:-educational-env}
export REGISTRY_NAME=${REGISTRY_NAME:-educationalacr}

# Verificar Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI no está instalado"
    exit 1
fi

# Login si es necesario
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}🔐 Iniciando sesión en Azure...${NC}"
    az login --output none
fi

# Despliegue rápido
echo -e "${YELLOW}📦 Creando recursos...${NC}"

# Grupo de recursos
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

# Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true --output none
az acr login --name $REGISTRY_NAME --output none

# Build y push
docker build -t educational-app:latest .
docker tag educational-app:latest $REGISTRY_NAME.azurecr.io/educational-app:latest
docker push $REGISTRY_NAME.azurecr.io/educational-app:latest

# Entorno Container Apps
az containerapp env create --name $CONTAINERAPPS_ENVIRONMENT --resource-group $RESOURCE_GROUP --location $LOCATION --output none

# Aplicación principal
echo -e "${YELLOW}🚀 Desplegando aplicación...${NC}"

# Preparar variables para Azure
AZURE_VARS=""
for var in $(cat .env | grep -v '^#' | grep '=' | cut -d'=' -f1); do
    if [ -n "${!var}" ]; then
        AZURE_VARS+="$var=${!var} "
    fi
done

az containerapp create \
    --name educational-api \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINERAPPS_ENVIRONMENT \
    --image $REGISTRY_NAME.azurecr.io/educational-app:latest \
    --cpu 1.0 --memory 2Gi \
    --min-replicas 1 --max-replicas 5 \
    --env-vars $AZURE_VARS \
    --ingress external \
    --target-port 8000 \
    --transport http \
    --registry-server $REGISTRY_NAME.azurecr.io \
    --registry-username $REGISTRY_NAME \
    --registry-password $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv) \
    --output none

# Obtener URL
APP_URL=$(az containerapp show --name educational-api --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

echo -e "${GREEN}✅ Despliegue completado!${NC}"
echo -e "${GREEN}🌐 URL: https://$APP_URL${NC}"
echo -e "${GREEN}📊 Health: https://$APP_URL/health${NC}"
echo -e "${GREEN}📖 Docs: https://$APP_URL/docs${NC}"