#!/bin/bash

# Azure Container Apps - Quick Deployment Script
# Educational System - One-Command Deployment

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
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

# Function to print usage
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help          Show this help message"
    echo "  --setup-only    Only setup Azure resources, don't deploy"
    echo "  --deploy-only   Only deploy application, skip setup"
    echo "  --region        Specify Azure region (default: eastus)"
    echo "  --resource-group Specify resource group name (default: educational-system-rg)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full deployment"
    echo "  $0 --setup-only       # Setup Azure resources only"
    echo "  $0 --region westus2   # Deploy to westus2 region"
}

# Default values
RESOURCE_GROUP="educational-system-rg"
LOCATION="eastus"
SETUP_ONLY=false
DEPLOY_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            print_usage
            exit 0
            ;;
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --deploy-only)
            DEPLOY_ONLY=true
            shift
            ;;
        --region)
            LOCATION="$2"
            shift 2
            ;;
        --resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Azure CLI
    if ! command -v az > /dev/null 2>&1; then
        echo "❌ Azure CLI is not installed. Please install it:"
        echo "   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker > /dev/null 2>&1; then
        echo "❌ Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    # Check if logged into Azure
    if ! az account show > /dev/null 2>&1; then
        echo "🔄 Logging into Azure..."
        az login
    fi
    
    print_success "Prerequisites verified ✅"
}

# Setup Azure resources
setup_azure_resources() {
    print_header "Setting up Azure Resources"
    
    # Create resource group
    print_info "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
    
    # Create container registry
    print_info "Creating container registry: educationalacr..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name educationalacr \
        --sku Basic \
        --admin-enabled true
    
    # Create container apps environment
    print_info "Creating container apps environment..."
    az containerapp env create \
        --name educational-env \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
    
    print_success "Azure resources created successfully ✅"
}

# Build and push Docker image
build_and_push_image() {
    print_header "Building and Pushing Docker Image"
    
    # Login to registry
    print_info "Logging into Azure Container Registry..."
    az acr login --name educationalacr
    
    # Build image
    print_info "Building Docker image..."
    docker build -t educational-app:latest -f docker/Dockerfile.production .
    
    # Tag image
    docker tag educational-app:latest educationalacr.azurecr.io/educational-app:latest
    
    # Push image
    print_info "Pushing image to Azure Container Registry..."
    docker push educationalacr.azurecr.io/educational-app:latest
    
    print_success "Docker image built and pushed successfully ✅"
}

# Deploy the application
deploy_application() {
    print_header "Deploying Educational System"
    
    # Deploy PostgreSQL
    print_info "Deploying PostgreSQL..."
    az containerapp create \
        --name educational-postgres \
        --resource-group $RESOURCE_GROUP \
        --environment educational-env \
        --image postgres:15-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            POSTGRES_DB=educational_system \
            POSTGRES_USER=admin \
            POSTGRES_PASSWORD=secure_password_2024 \
        --ingress internal \
        --target-port 5432 \
        --transport tcp
    
    # Deploy Redis
    print_info "Deploying Redis..."
    az containerapp create \
        --name educational-redis \
        --resource-group $RESOURCE_GROUP \
        --environment educational-env \
        --image redis:7-alpine \
        --cpu 0.25 --memory 0.5Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            REDIS_PASSWORD=redis_password_2024 \
        --ingress internal \
        --target-port 6379 \
        --transport tcp \
        --args redis-server --appendonly yes --requirepass $(REDIS_PASSWORD) --maxmemory 512mb --maxmemory-policy allkeys-lru
    
    # Deploy RabbitMQ
    print_info "Deploying RabbitMQ..."
    az containerapp create \
        --name educational-rabbitmq \
        --resource-group $RESOURCE_GROUP \
        --environment educational-env \
        --image rabbitmq:3-management-alpine \
        --cpu 0.5 --memory 1Gi \
        --min-replicas 1 --max-replicas 1 \
        --env-vars \
            RABBITMQ_DEFAULT_USER=admin \
            RABBITMQ_DEFAULT_PASS=rabbit_password_2024 \
        --ingress internal \
        --target-port 5672 \
        --transport tcp
    
    # Deploy main application
    print_info "Deploying Educational System API..."
    az containerapp create \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --environment educational-env \
        --image educationalacr.azurecr.io/educational-app:latest \
        --cpu 1.0 --memory 2Gi \
        --min-replicas 2 --max-replicas 10 \
        --env-vars \
            DATABASE_URL="postgresql://admin:secure_password_2024@educational-postgres:5432/educational_system" \
            REDIS_URL="redis://default:redis_password_2024@educational-redis:6379/0" \
            RABBITMQ_URL="amqp://admin:rabbit_password_2024@educational-rabbitmq:5672/" \
            ENVIRONMENT=production \
            WORKERS=4 \
            GROQ_API_KEY=your-groq-api-key \
            OPENAI_API_KEY=your-openai-api-key \
        --ingress external \
        --target-port 8000 \
        --transport http \
        --registry-server educationalacr.azurecr.io \
        --registry-username educationalacr \
        --registry-password $(az acr credential show --name educationalacr --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)
    
    # Configure auto-scaling
    print_info "Configuring auto-scaling..."
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name cpu-scaling \
        --scale-rule-type cpu \
        --scale-rule-metadata "metricType=Utilization" "metricValue=70"
    
    # Add memory scaling
    az containerapp update \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name memory-scaling \
        --scale-rule-type memory \
        --scale-rule-metadata "metricType=Utilization" "metricValue=80"
    
    print_success "Application deployed successfully ✅"
}

# Get application info
get_application_info() {
    print_header "Application Information"
    
    # Get application URL
    APP_URL=$(az containerapp show \
        --name educational-api \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "======================"
    echo ""
    echo "Application URL: https://$APP_URL"
    echo "Health Check: https://$APP_URL/health"
    echo "API Documentation: https://$APP_URL/docs"
    echo ""
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo ""
    echo "Services deployed:"
    echo "- PostgreSQL: educational-postgres"
    echo "- Redis: educational-redis"
    echo "- RabbitMQ: educational-rabbitmq"
    echo "- API: educational-api (2-10 replicas)"
    echo ""
    
    # Save deployment info
    cat << DEPLOYMENT_INFO > deployment-info.txt
Azure Container Apps Deployment - Educational System
=================================================

Resource Group: $RESOURCE_GROUP
Location: $LOCATION
Container Registry: educationalacr.azurecr.io
Application URL: https://$APP_URL

Services:
- API: educational-api (2-10 replicas)
- PostgreSQL: educational-postgres (1 replica)
- Redis: educational-redis (1 replica)
- RabbitMQ: educational-rabbitmq (1 replica)

Environment Variables:
- DATABASE_URL: postgresql://admin:secure_password_2024@educational-postgres:5432/educational_system
- REDIS_URL: redis://default:redis_password_2024@educational-redis:6379/0
- RABBITMQ_URL: amqp://admin:rabbit_password_2024@educational-rabbitmq:5672/

Deployment Date: $(date)
DEPLOYMENT_INFO
    
    print_success "Deployment information saved to deployment-info.txt"
}

# Main execution
main() {
    print_header "Azure Container Apps - Quick Deployment"
    echo "Deploying Educational System to Azure Container Apps..."
    echo ""
    
    check_prerequisites
    
    if [[ "$DEPLOY_ONLY" == "true" ]]; then
        build_and_push_image
        deploy_application
    elif [[ "$SETUP_ONLY" == "true" ]]; then
        setup_azure_resources
    else
        setup_azure_resources
        build_and_push_image
        deploy_application
    fi
    
    get_application_info
    
    print_header "Next Steps"
    echo ""
    echo "1. Update environment variables with your actual API keys:"
    echo "   az containerapp update --name educational-api --resource-group $RESOURCE_GROUP --set-env-vars GROQ_API_KEY=your-key OPENAI_API_KEY=your-key"
    echo ""
    echo "2. Monitor your application:"
    echo "   az containerapp logs show --name educational-api --resource-group $RESOURCE_GROUP --follow"
    echo ""
    echo "3. Scale your application:"
    echo "   az containerapp update --name educational-api --resource-group $RESOURCE_GROUP --min-replicas 5"
    echo ""
    echo "4. View metrics:"
    echo "   az containerapp show --name educational-api --resource-group $RESOURCE_GROUP"
    echo ""
}

# Execute main function
main "$@"