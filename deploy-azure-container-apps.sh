#!/bin/bash

# Azure Container Apps Deployment Script
# Educational System - Production Deployment
# This script deploys the complete educational system to Azure Container Apps

set -e

# Configuration
RESOURCE_GROUP="educational-system-rg"
LOCATION="eastus"
CONTAINERAPPS_ENVIRONMENT="educational-env"
REGISTRY_NAME="educationalacr"
API_APP_NAME="educational-api"
POSTGRES_APP_NAME="educational-postgres"
REDIS_APP_NAME="educational-redis"
RABBITMQ_APP_NAME="educational-rabbitmq"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first:"
        echo "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        exit 1
    fi
}

# Login to Azure
azure_login() {
    print_header "Logging into Azure"
    az login
    az account show
}

# Create Resource Group
create_resource_group() {
    print_header "Creating Resource Group: $RESOURCE_GROUP"
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION
    print_success "Resource group created"
}

# Create Container Registry
create_container_registry() {
    print_header "Creating Container Registry: $REGISTRY_NAME"
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $REGISTRY_NAME \
        --sku Basic \
        --admin-enabled true
    
    # Get login server
    LOGIN_SERVER=$(az acr show \
        --name $REGISTRY_NAME \
        --resource-group $RESOURCE_GROUP \
        --query loginServer \
        --output tsv)
    
    # Login to ACR
    az acr login --name $REGISTRY_NAME
    
    print_success "Container registry created: $LOGIN_SERVER"
}

# Build and push Docker images
build_and_push_images() {
    print_header "Building and pushing Docker images"
    
    # Build the main application
    docker build -t educational-app:latest -f docker/Dockerfile.production .
    
    # Tag and push to ACR
    docker tag educational-app:latest $REGISTRY_NAME.azurecr.io/educational-app:latest
    docker push $REGISTRY_NAME.azurecr.io/educational-app:latest
    
    print_success "Images built and pushed successfully"
}

# Create Container Apps Environment
create_container_apps_environment() {
    print_header "Creating Container Apps Environment"
    az containerapp env create \
        --name $CONTAINERAPPS_ENVIRONMENT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
    print_success "Container apps environment created"
}

# Deploy PostgreSQL
deploy_postgres() {
    print_header "Deploying PostgreSQL"
    
    # Create PostgreSQL Container App
    az containerapp create \
        --name $POSTGRES_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image postgres:15-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            POSTGRES_DB=educational_system \
            POSTGRES_USER=admin \
            POSTGRES_PASSWORD=secure_password_2024 \
            POSTGRES_REPLICA_USER=replica \
            POSTGRES_REPLICA_PASSWORD=replica_password_2024 \
        --ingress internal \
        --target-port 5432 \
        --transport tcp
    
    print_success "PostgreSQL deployed"
}

# Deploy Redis
deploy_redis() {
    print_header "Deploying Redis"
    
    # Create Redis Container App
    az containerapp create \
        --name $REDIS_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image redis:7-alpine \
        --cpu 0.25 --memory 0.5Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            REDIS_PASSWORD=redis_password_2024 \
        --ingress internal \
        --target-port 6379 \
        --transport tcp
    
    print_success "Redis deployed"
}

# Deploy RabbitMQ
deploy_rabbitmq() {
    print_header "Deploying RabbitMQ"
    
    # Create RabbitMQ Container App
    az containerapp create \
        --name $RABBITMQ_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image rabbitmq:3-management-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            RABBITMQ_DEFAULT_USER=admin \
            RABBITMQ_DEFAULT_PASS=rabbit_password_2024 \
        --ingress internal \
        --target-port 5672 \
        --transport tcp
    
    print_success "RabbitMQ deployed"
}

# Deploy main application
deploy_api() {
    print_header "Deploying Educational System API"
    
    # Wait for dependent services
    print_info "Waiting for dependent services to be ready..."
    sleep 30
    
    # Get service URLs
    POSTGRES_URL="postgresql://admin:secure_password_2024@$POSTGRES_APP_NAME.internal:5432/educational_system"
    REDIS_URL="redis://default:redis_password_2024@$REDIS_APP_NAME.internal:6379/0"
    RABBITMQ_URL="amqp://admin:rabbit_password_2024@$RABBITMQ_APP_NAME.internal:5672/"
    
    # Create API Container App
    az containerapp create \
        --name $API_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINERAPPS_ENVIRONMENT \
        --image $REGISTRY_NAME.azurecr.io/educational-app:latest \
        --cpu 1.0 --memory 2Gi \
        --min-replicas 2 --max-replicas 10 \
        --env-vars \
            DATABASE_URL="$POSTGRES_URL" \
            REDIS_URL="$REDIS_URL" \
            RABBITMQ_URL="$RABBITMQ_URL" \
            ENVIRONMENT=production \
            WORKERS=4 \
            GROQ_API_KEY=your-groq-api-key \
            OPENAI_API_KEY=your-openai-api-key \
        --ingress external \
        --target-port 8000 \
        --transport http \
        --registry-server $REGISTRY_NAME.azurecr.io \
        --registry-username $REGISTRY_NAME \
        --registry-password $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)
    
    print_success "Educational System API deployed"
}

# Configure scaling
configure_scaling() {
    print_header "Configuring Auto-scaling"
    
    # Configure auto-scaling rules
    az containerapp update \
        --name $API_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name cpu-scaling \
        --scale-rule-type cpu \
        --scale-rule-metadata \
            "metricType=Utilization" \
            "metricValue=70" \
        --scale-rule-auth
    
    print_success "Auto-scaling configured"
}

# Get application URL
get_application_url() {
    print_header "Getting Application URL"
    
    # Get the FQDN of the application
    APP_URL=$(az containerapp show \
        --name $API_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    print_success "Application deployed successfully!"
    echo ""
    echo "Application URL: https://$APP_URL"
    echo ""
    echo "Health Check: https://$APP_URL/health"
    echo "API Documentation: https://$APP_URL/docs"
    echo ""
    echo "Database: $POSTGRES_APP_NAME"
    echo "Cache: $REDIS_APP_NAME"
    echo "Message Queue: $RABBITMQ_APP_NAME"
    echo ""
}

# Main deployment function
main() {
    print_header "Azure Container Apps - Educational System Deployment"
    
    check_azure_cli
    azure_login
    create_resource_group
    create_container_registry
    build_and_push_images
    create_container_apps_environment
    deploy_postgres
    deploy_redis
    deploy_rabbitmq
    deploy_api
    configure_scaling
    get_application_url
    
    print_header "Deployment Complete!"
    echo "Your educational system is now running on Azure Container Apps"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi