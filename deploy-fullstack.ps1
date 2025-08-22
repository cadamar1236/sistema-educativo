# Script de despliegue fullstack (Frontend + Backend integrados)
param(
    [string]$AppName = "educational-fullstack",
    [string]$ResourceGroup = "",
    [string]$RegistryName = "eduacr9303"
)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "DESPLIEGUE FULLSTACK (Next.js + FastAPI)" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Verificar autenticación
$account = az account show --query name --output tsv 2>$null
if (!$account) {
    Write-Host "Iniciando sesión en Azure..." -ForegroundColor Yellow
    az login
}

# Buscar grupo de recursos si no se especifica
if ([string]::IsNullOrEmpty($ResourceGroup)) {
    Write-Host "Buscando grupo de recursos..." -ForegroundColor Blue
    $ResourceGroup = az acr show --name $RegistryName --query resourceGroup --output tsv 2>$null
    if ([string]::IsNullOrEmpty($ResourceGroup)) {
        Write-Error "No se encontró el Container Registry $RegistryName"
        exit 1
    }
}

Write-Host "Configuración:" -ForegroundColor Yellow
Write-Host "- App: $AppName" -ForegroundColor White
Write-Host "- Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "- Registry: $RegistryName" -ForegroundColor White

# Habilitar admin en registry y login
Write-Host "Configurando registry..." -ForegroundColor Blue
az acr update -n $RegistryName --admin-enabled true --output none
az acr login --name $RegistryName

# Construir imagen fullstack
$registryServer = "$RegistryName.azurecr.io"
$imageName = "$registryServer/$AppName`:latest"

Write-Host "Construyendo imagen fullstack..." -ForegroundColor Blue
Write-Host "Esto puede tardar varios minutos (compilando frontend + backend)..." -ForegroundColor Yellow

# Usar Dockerfile fullstack
docker build -f Dockerfile.fullstack -t $imageName .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error construyendo imagen fullstack"
    exit 1
}

Write-Host "Subiendo imagen al registry..." -ForegroundColor Blue
docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error subiendo imagen"
    exit 1
}

# Obtener detalles para deployment
$location = az acr show --name $RegistryName --query location --output tsv
$envName = "educational-env"
$registryPassword = az acr credential show --name $RegistryName --query passwords[0].value --output tsv

# Verificar/crear Container Apps Environment
$envExists = az containerapp env show --name $envName --resource-group $ResourceGroup --query name --output tsv 2>$null
if ([string]::IsNullOrEmpty($envExists)) {
    Write-Host "Creando entorno Container Apps..." -ForegroundColor Blue
    az containerapp env create --name $envName --resource-group $ResourceGroup --location $location --output none
}

# Verificar si la app existe
$appExists = az containerapp show --name $AppName --resource-group $ResourceGroup --query name --output tsv 2>$null

# Variables de entorno para fullstack
$envVars = @(
    "ENVIRONMENT=production"
    "PYTHONPATH=/app"
    "PORT=8000"
    "HOST=0.0.0.0"
    "FRONTEND_BUILD_DIR=/app/frontend/.next"
    "CORS_ORIGINS=[`"*`"]"
)

if ([string]::IsNullOrEmpty($appExists)) {
    Write-Host "Creando nueva Container App fullstack..." -ForegroundColor Blue
    
    az containerapp create `
        --name $AppName `
        --resource-group $ResourceGroup `
        --environment $envName `
        --image $imageName `
        --registry-server $registryServer `
        --registry-username $RegistryName `
        --registry-password $registryPassword `
        --target-port 8000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 5 `
        --cpu 2.0 `
        --memory 4.0Gi `
        --env-vars $envVars `
        --output none
} else {
    Write-Host "Actualizando Container App existente..." -ForegroundColor Blue
    
    az containerapp update `
        --name $AppName `
        --resource-group $ResourceGroup `
        --image $imageName `
        --cpu 2.0 `
        --memory 4.0Gi `
        --output none
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error desplegando Container App fullstack"
    exit 1
}

# Obtener URL de la aplicación
$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "DESPLIEGUE FULLSTACK COMPLETADO!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 APLICACION COMPLETA:" -ForegroundColor Cyan
Write-Host "   https://$appUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host "📱 ENDPOINTS PRINCIPALES:" -ForegroundColor Cyan
Write-Host "   Frontend (Next.js):  https://$appUrl/" -ForegroundColor White
Write-Host "   API Backend:         https://$appUrl/api/" -ForegroundColor White
Write-Host "   API Docs:            https://$appUrl/api/docs" -ForegroundColor White
Write-Host "   Health Check:        https://$appUrl/health" -ForegroundColor White
Write-Host ""
Write-Host "⚡ CAPACIDAD ESTIMADA:" -ForegroundColor Cyan
Write-Host "   CPU: 2.0 vCPUs" -ForegroundColor White
Write-Host "   RAM: 4.0 GB" -ForegroundColor White
Write-Host "   Usuarios simultáneos: ~200-500" -ForegroundColor White
Write-Host "   Auto-escalado: 1-5 réplicas" -ForegroundColor White
Write-Host ""
Write-Host "🔧 COMANDOS UTILES:" -ForegroundColor Yellow
Write-Host "   Logs: az containerapp logs show --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor Gray
Write-Host "   Estado: az containerapp show --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray
Write-Host ""
Write-Host "La aplicación puede tardar 2-3 minutos en estar completamente lista" -ForegroundColor Yellow
