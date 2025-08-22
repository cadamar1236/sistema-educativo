# Script de deployment para main_simple.py con frontend integrado
param(
    [string]$AppName = "educational-api",
    [string]$RegistryName = "eduacr9303"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT FULLSTACK - MAIN_SIMPLE.PY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Buscar grupo de recursos del registry
Write-Host "Buscando configuración existente..." -ForegroundColor Blue
$ResourceGroup = az acr show --name $RegistryName --query resourceGroup --output tsv 2>$null
if ([string]::IsNullOrEmpty($ResourceGroup)) {
    Write-Error "No se encontró el Container Registry $RegistryName"
    Write-Host "Registries disponibles:" -ForegroundColor Yellow
    az acr list --query "[].{Name:name, ResourceGroup:resourceGroup}" --output table
    exit 1
}

$location = az acr show --name $RegistryName --query location --output tsv
$registryServer = "$RegistryName.azurecr.io"

Write-Host "Configuración detectada:" -ForegroundColor Green
Write-Host "- App: $AppName" -ForegroundColor White
Write-Host "- Registry: $RegistryName" -ForegroundColor White
Write-Host "- Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "- Location: $location" -ForegroundColor White

# Verificar que tenemos el frontend
Write-Host "Verificando estructura del proyecto..." -ForegroundColor Blue
$hasBackend = Test-Path "src/main_simple.py"
$hasFrontend = Test-Path "julia-frontend/package.json"

if (!$hasBackend) {
    Write-Error "No se encontró src/main_simple.py"
    exit 1
}

if (!$hasFrontend) {
    Write-Warning "No se encontró julia-frontend/package.json - solo se desplegará el backend"
}

Write-Host "✅ Backend encontrado: src/main_simple.py" -ForegroundColor Green
if ($hasFrontend) {
    Write-Host "✅ Frontend encontrado: julia-frontend/" -ForegroundColor Green
} else {
    Write-Host "⚠️ Frontend no encontrado" -ForegroundColor Yellow
}

# Habilitar admin en registry
Write-Host "Configurando Container Registry..." -ForegroundColor Blue
az acr update -n $RegistryName --admin-enabled true --output none
az acr login --name $RegistryName

# Construir imagen
Write-Host "Construyendo imagen fullstack..." -ForegroundColor Blue
$imageName = "$registryServer/$AppName`:latest"

# Usar Dockerfile.simple si existe, sino Dockerfile.fullstack
$dockerFile = "Dockerfile.simple"
if (!(Test-Path $dockerFile)) {
    $dockerFile = "Dockerfile.fullstack"
    if (!(Test-Path $dockerFile)) {
        $dockerFile = "Dockerfile"
    }
}

Write-Host "Usando: $dockerFile" -ForegroundColor Yellow

# Construir con más verbose para debug
docker build -f $dockerFile -t $imageName . --progress=plain

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error construyendo imagen Docker"
    exit 1
}

# Push imagen
Write-Host "Subiendo imagen al registry..." -ForegroundColor Blue
docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error subiendo imagen"
    exit 1
}

# Verificar Container Apps Environment
$envName = "educational-env"
$envExists = az containerapp env show --name $envName --resource-group $ResourceGroup --query name --output tsv 2>$null

if ([string]::IsNullOrEmpty($envExists)) {
    Write-Host "Creando Container Apps Environment..." -ForegroundColor Blue
    az containerapp env create --name $envName --resource-group $ResourceGroup --location $location --output none
    Write-Host "Environment creado: $envName" -ForegroundColor Green
}

# Obtener credenciales
$registryPassword = az acr credential show --name $RegistryName --query passwords[0].value --output tsv

# Variables de entorno específicas para main_simple
$envVars = @(
    "ENVIRONMENT=production"
    "PYTHONPATH=/app"
    "PORT=8000" 
    "HOST=0.0.0.0"
    "DEBUG=false"
)

# Verificar si la app existe
$appExists = az containerapp show --name $AppName --resource-group $ResourceGroup --query name --output tsv 2>$null

if ([string]::IsNullOrEmpty($appExists)) {
    Write-Host "Creando nueva Container App..." -ForegroundColor Blue
    
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
        --cpu 1.0 `
        --memory 2.0Gi `
        --env-vars $envVars `
        --output none
        
} else {
    Write-Host "Actualizando Container App existente..." -ForegroundColor Blue
    
    az containerapp update `
        --name $AppName `
        --resource-group $ResourceGroup `
        --image $imageName `
        --output none
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error desplegando Container App"
    exit 1
}

# Obtener URL
Write-Host "Obteniendo URL de la aplicación..." -ForegroundColor Blue
$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

# Mostrar resultado
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "🚀 DEPLOYMENT COMPLETADO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URL de tu aplicación:" -ForegroundColor Yellow
Write-Host "   https://$appUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 API Endpoints disponibles:" -ForegroundColor Yellow
Write-Host "   • API Docs: https://$appUrl/docs" -ForegroundColor White
Write-Host "   • API Schema: https://$appUrl/openapi.json" -ForegroundColor White
Write-Host "   • Health Check: https://$appUrl/health" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   • Ver logs: az containerapp logs show --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor White
Write-Host "   • Reiniciar: az containerapp revision restart --name $AppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host "   • Escalar: az containerapp update --name $AppName --resource-group $ResourceGroup --min-replicas 2 --max-replicas 10" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Capacidad estimada con configuración actual:" -ForegroundColor Cyan
Write-Host "   • CPU: 1.0 cores, RAM: 2.0GB" -ForegroundColor White
Write-Host "   • Usuarios simultáneos: ~100-200 (dependiendo de uso)" -ForegroundColor White
Write-Host "   • Escalado automático: 1-5 instancias" -ForegroundColor White
Write-Host ""
Write-Host "🔥 Para más capacidad, ejecuta:" -ForegroundColor Red
Write-Host "   az containerapp update --name $AppName --resource-group $ResourceGroup --cpu 2.0 --memory 4.0Gi --max-replicas 10" -ForegroundColor Yellow
