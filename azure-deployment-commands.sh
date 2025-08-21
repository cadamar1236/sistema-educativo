#!/bin/bash

# Azure Container Apps Deployment Commands
# Educational System - Production Deployment
# Execute these commands step by step

# =============================================================================
# PREREQUISITES
# =============================================================================
# 1. Azure CLI installed
# 2. Docker Desktop installed
# 3. Git repository with your code
# 4. Valid Azure subscription

# =============================================================================
# STEP 1: LOGIN TO AZURE
# =============================================================================
print_header "Step 1: Azure Login"
echo "Logging into Azure..."
az login

# Set subscription if you have multiple
# az account set --subscription "your-subscription-id"

# =============================================================================
# STEP 2: CREATE RESOURCE GROUP
# =============================================================================
print_header "Step 2: Create Resource Group"
az group create \
    --name educational-system-rg \
    --location eastus

# =============================================================================
# STEP 3: CREATE CONTAINER REGISTRY
# =============================================================================
print_header "Step 3: Create Container Registry"
az acr create \
    --resource-group educational-system-rg \
    --name educationalacr \
    --sku Basic \
    --admin-enabled true

# Login to registry
az acr login --name educationalacr

# =============================================================================
# STEP 4: BUILD AND PUSH DOCKER IMAGE
# =============================================================================
print_header "Step 4: Build and Push Docker Image"

# Build the image
docker build -t educational-app:latest -f docker/Dockerfile.production .

# Tag with registry
docker tag educational-app:latest educationalacr.azurecr.io/educational-app:latest

# Push to Azure Container Registry
docker push educationalacr.azurecr.io/educational-app:latest

# =============================================================================
# STEP 5: CREATE CONTAINER APPS ENVIRONMENT
# =============================================================================
print_header "Step 5: Create Container Apps Environment"

# Create the environment
az containerapp env create \
    --name educational-env \
    --resource-group educational-system-rg \
    --location eastus

# =============================================================================
# STEP 6: DEPLOY POSTGRESQL
# =============================================================================
print_header "Step 6: Deploy PostgreSQL"

# Create PostgreSQL
az containerapp create \
    --name educational-postgres \
    --resource-group educational-system-rg \
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

# =============================================================================
# STEP 7: DEPLOY REDIS
# =============================================================================
print_header "Step 7: Deploy Redis"

# Create Redis
az containerapp create \
    --name educational-redis \
    --resource-group educational-system-rg \
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

# =============================================================================
# STEP 8: DEPLOY RABBITMQ
# =============================================================================
print_header "Step 8: Deploy RabbitMQ"

# Create RabbitMQ
az containerapp create \
    --name educational-rabbitmq \
    --resource-group educational-system-rg \
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

# =============================================================================
# STEP 9: DEPLOY MAIN APPLICATION
# =============================================================================
print_header "Step 9: Deploy Educational System API"

# Create the main application
az containerapp create \
    --name educational-api \
    --resource-group educational-system-rg \
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
    --registry-password $(az acr credential show --name educationalacr --resource-group educational-system-rg --query passwords[0].value --output tsv)

# =============================================================================
# STEP 10: CONFIGURE SCALING
# =============================================================================
print_header "Step 10: Configure Auto-scaling"

# Configure CPU scaling
az containerapp update \
    --name educational-api \
    --resource-group educational-system-rg \
    --scale-rule-name cpu-scaling \
    --scale-rule-type cpu \
    --scale-rule-metadata "metricType=Utilization" "metricValue=70"

# Configure memory scaling
az containerapp update \
    --name educational-api \
    --resource-group educational-system-rg \
    --scale-rule-name memory-scaling \
    --scale-rule-type memory \
    --scale-rule-metadata "metricType=Utilization" "metricValue=80"

# =============================================================================
# STEP 11: GET APPLICATION URL
# =============================================================================
print_header "Step 11: Get Application URL"

# Get the application URL
APP_URL=$(az containerapp show \
    --name educational-api \
    --resource-group educational-system-rg \
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
echo "Services:"
echo "- PostgreSQL: educational-postgres"
echo "- Redis: educational-redis"
echo "- RabbitMQ: educational-rabbitmq"
echo ""

# =============================================================================
# USEFUL COMMANDS
# =============================================================================
cat << 'EOF'

USEFUL AZURE COMMANDS:
===================

# View logs
az containerapp logs show --name educational-api --resource-group educational-system-rg --follow

# Monitor scaling
az containerapp show --name educational-api --resource-group educational-system-rg --query properties.template.scale

# Update environment variables
az containerapp update --name educational-api --resource-group educational-system-rg --set-env-vars NEW_VAR=new_value

# Scale manually
az containerapp update --name educational-api --resource-group educational-system-rg --min-replicas 5

# Restart application
az containerapp restart --name educational-api --resource-group educational-system-rg

# View resource usage
az containerapp show --name educational-api --resource-group educational-system-rg --query properties.template.containers[0].resources

# Delete all resources (cleanup)
az group delete --name educational-system-rg --yes

EOF

# =============================================================================
# SAVE DEPLOYMENT INFO
# =============================================================================
cat << DEPLOYMENT_INFO > deployment-info.txt
Azure Container Apps Deployment - Educational System
=================================================

Resource Group: educational-system-rg
Location: eastus
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