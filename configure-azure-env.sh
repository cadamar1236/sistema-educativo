#!/bin/bash

# Script interactivo para configurar variables de entorno para Azure Container Apps
# Educational System - Configuration Tool

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Función para generar contraseñas seguras
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Función para solicitar input con validación
prompt_input() {
    local prompt=$1
    local default=$2
    local required=${3:-false}
    
    while true; do
        if [ -n "$default" ]; then
            echo -e "${BLUE}?${NC} $prompt ${YELLOW}($default)${NC}: "
            read -r input
            input=${input:-$default}
        else
            echo -e "${BLUE}?${NC} $prompt: "
            read -r input
        fi
        
        if [ "$required" = true ] && [ -z "$input" ]; then
            print_error "Este campo es obligatorio"
            continue
        fi
        
        echo "$input"
        break
    done
}

# Función para solicitar contraseñas
prompt_password() {
    local prompt=$1
    local generate=${2:-false}
    
    if [ "$generate" = true ]; then
        password=$(generate_password)
        echo -e "${GREEN}Contraseña generada automáticamente: $password${NC}"
        echo "$password"
        return
    fi
    
    while true; do
        echo -e "${BLUE}?${NC} $prompt (dejar vacío para generar automáticamente): "
        read -s password
        echo
        
        if [ -z "$password" ]; then
            password=$(generate_password)
            echo -e "${GREEN}Contraseña generada automáticamente: $password${NC}"
        fi
        
        echo -e "${BLUE}?${NC} Confirmar contraseña: "
        read -s confirm
        echo
        
        if [ "$password" = "$confirm" ]; then
            echo "$password"
            break
        else
            print_error "Las contraseñas no coinciden. Inténtalo de nuevo."
        fi
    done
}

# Función para configurar Azure
configure_azure() {
    print_header "Configuración de Azure"
    
    RESOURCE_GROUP=$(prompt_input "Nombre del grupo de recursos" "educational-system-rg" true)
    LOCATION=$(prompt_input "Ubicación de Azure" "eastus" true)
    REGISTRY_NAME=$(prompt_input "Nombre del Container Registry" "educationalacr" true)
    ENVIRONMENT_NAME=$(prompt_input "Nombre del entorno de Container Apps" "educational-env" true)
    
    print_success "Configuración de Azure completada"
}

# Función para configurar APIs externas
configure_apis() {
    print_header "Configuración de APIs Externas"
    print_warning "Por favor, proporciona tus claves de API reales"
    
    GROQ_API_KEY=$(prompt_input "Clave de API de Groq" "" true)
    OPENAI_API_KEY=$(prompt_input "Clave de API de OpenAI" "" true)
    ANTHROPIC_API_KEY=$(prompt_input "Clave de API de Anthropic (opcional)" "")
}

# Función para configurar contraseñas
configure_passwords() {
    print_header "Configuración de Contraseñas"
    print_info "Se generarán contraseñas seguras automáticamente"
    
    POSTGRES_PASSWORD=$(prompt_password "Contraseña para PostgreSQL" true)
    REDIS_PASSWORD=$(prompt_password "Contraseña para Redis" true)
    RABBITMQ_PASSWORD=$(prompt_password "Contraseña para RabbitMQ" true)
    JWT_SECRET=$(prompt_password "JWT Secret (secreto de autenticación)" true)
    
    print_success "Contraseñas configuradas"
}

# Función para crear el archivo de configuración
create_env_file() {
    print_header "Creando archivo de configuración"
    
    cat > .env.azure << EOF
# Azure Configuration
RESOURCE_GROUP=$RESOURCE_GROUP
LOCATION=$LOCATION
CONTAINERAPPS_ENVIRONMENT=$ENVIRONMENT_NAME
REGISTRY_NAME=$REGISTRY_NAME

# Application Configuration
ENVIRONMENT=production
WORKERS=4
UVICORN_WORKERS=4
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# Database
POSTGRES_DB=educational_system
POSTGRES_USER=admin
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=educational-postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://admin:$POSTGRES_PASSWORD@educational-postgres:5432/educational_system

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_HOST=educational-redis
REDIS_PORT=6379
REDIS_URL=redis://default:$REDIS_PASSWORD@educational-redis:6379/0

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD
RABBITMQ_HOST=educational-rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_URL=amqp://admin:$RABBITMQ_PASSWORD@educational-rabbitmq:5672/

# API Keys
GROQ_API_KEY=$GROQ_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Security
SECRET_KEY=$JWT_SECRET
JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
ENABLE_TRACING=true

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,md
EOF

    print_success "Archivo .env.azure creado exitosamente"
}

# Función para crear script de aplicación de configuración
create_apply_script() {
    cat > apply-env-config.sh << 'EOF'
#!/bin/bash

# Script para aplicar las configuraciones al despliegue de Azure

# Cargar variables de entorno
if [ -f .env.azure ]; then
    export $(cat .env.azure | xargs)
    echo "Variables de entorno cargadas de .env.azure"
else
    echo "Error: .env.azure no encontrado. Ejecute ./configure-azure-env.sh primero"
    exit 1
fi

# Crear secrets en Azure
print_header "Aplicando configuración a Azure Container Apps"

# Verificar si estás logueado en Azure
if ! az account show &> /dev/null; then
    echo "Por favor, inicia sesión en Azure primero:"
    az login
fi

# Establecer variables como secretos de Azure
az containerapp secret set \
  --name educational-api \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    postgres-password=$POSTGRES_PASSWORD \
    redis-password=$REDIS_PASSWORD \
    rabbitmq-password=$RABBITMQ_PASSWORD \
    groq-api-key=$GROQ_API_KEY \
    openai-api-key=$OPENAI_API_KEY \
    jwt-secret=$JWT_SECRET

echo "Configuración aplicada exitosamente"
EOF

    chmod +x apply-env-config.sh
    print_success "Script apply-env-config.sh creado"
}

# Función para mostrar resumen
show_summary() {
    print_header "Resumen de Configuración"
    
    echo -e "${BLUE}Grupo de Recursos:${NC} $RESOURCE_GROUP"
    echo -e "${BLUE}Ubicación:${NC} $LOCATION"
    echo -e "${BLUE}Container Registry:${NC} $REGISTRY_NAME"
    echo -e "${BLUE}Entorno:${NC} $ENVIRONMENT_NAME"
    echo -e "${BLUE}PostgreSQL Password:${NC} ${POSTGRES_PASSWORD:0:3}***"
    echo -e "${BLUE}Redis Password:${NC} ${REDIS_PASSWORD:0:3}***"
    echo -e "${BLUE}RabbitMQ Password:${NC} ${RABBITMQ_PASSWORD:0:3}***"
    echo -e "${BLUE}Groq API:${NC} ${GROQ_API_KEY:0:8}***"
    echo -e "${BLUE}OpenAI API:${NC} ${OPENAI_API_KEY:0:8}***"
    
    echo ""
    print_info "Archivos creados:"
    echo "  - .env.azure (archivo de configuración principal)"
    echo "  - apply-env-config.sh (script para aplicar configuración)"
    echo "  - .env.azure.template (plantilla de ejemplo)"
    
    echo ""
    print_warning "IMPORTANTE: Guarda tus claves de API de forma segura"
    print_info "Para aplicar la configuración al despliegue, ejecuta:"
    echo "  ./apply-env-config.sh"
}

# Función principal
main() {
    print_header "Configurador de Variables de Entorno para Azure Container Apps"
    echo ""
    echo "Este script te ayudará a configurar todas las variables de entorno"
    echo "necesarias para desplegar tu sistema educativo en Azure Container Apps"
    echo ""
    
    read -p "¿Desea continuar con la configuración? (s/n): " confirm
    if [[ $confirm != [sS] ]]; then
        echo "Configuración cancelada"
        exit 1
    fi
    
    configure_azure
    configure_apis
    configure_passwords
    create_env_file
    create_apply_script
    show_summary
    
    print_success "Configuración completada exitosamente!"
    print_info "Ahora puedes ejecutar el despliegue con: ./quick-deploy-azure.sh"
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi