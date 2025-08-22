# Script de deployment principal - Usa el Dockerfile principal
param(
    [string]$AppName = "educational-api",
    [string]$RegistryName = "eduacr9303"
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🚀 DEPLOYMENT COMPLETO - DOCKERFILE PRINCIPAL" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Configuración automática
Write-Host "Detectando configuración..." -ForegroundColor Blue
$ResourceGroup = az acr show --name $RegistryName --query resourceGroup --output tsv 2>$null

if (!$ResourceGroup) {
    Write-Error "❌ Registry '$RegistryName' no encontrado"
    Write-Host ""
    Write-Host "Registries disponibles:" -ForegroundColor Yellow
    az acr list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location}" --output table 2>$null
    exit 1
}

$location = az acr show --name $RegistryName --query location --output tsv
$registryServer = "$RegistryName.azurecr.io"

Write-Host ""
Write-Host "✅ Configuración detectada:" -ForegroundColor Green
Write-Host "   📦 App: $AppName" -ForegroundColor White
Write-Host "   🗂️  Registry: $RegistryName" -ForegroundColor White
Write-Host "   🏗️  Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "   🌍 Location: $location" -ForegroundColor White

# Verificar archivos críticos
Write-Host ""
Write-Host "Verificando estructura del proyecto..." -ForegroundColor Blue

$checks = @{
    "Backend (main_simple.py)" = Test-Path "src/main_simple.py"
    "Requirements.txt" = Test-Path "requirements.txt"
    "Frontend (package.json)" = Test-Path "julia-frontend/package.json"
    "Dockerfile principal" = Test-Path "Dockerfile"
}

$allGood = $true
foreach ($check in $checks.GetEnumerator()) {
    $status = if ($check.Value) { "✅" } else { "❌"; $allGood = $false }
    $color = if ($check.Value) { "Green" } else { "Red" }
    Write-Host "   $status $($check.Key)" -ForegroundColor $color
}

if (!$allGood) {
    Write-Error "❌ Faltan archivos críticos. Revisa la estructura del proyecto."
    exit 1
}

# Autenticación y preparación
Write-Host ""
Write-Host "Preparando deployment..." -ForegroundColor Blue
az acr login --name $RegistryName

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en login al registry. Verifica tu autenticación Azure."
    exit 1
}

# Build de la imagen
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$imageName = "$registryServer/$AppName`:v$timestamp"

Write-Host ""
Write-Host "🏗️ Construyendo imagen completa..." -ForegroundColor Blue
Write-Host "   📦 Imagen: $imageName" -ForegroundColor Cyan

# Build con logs detallados
docker build -t $imageName . --no-cache --progress=plain

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error construyendo imagen Docker"
    Write-Host ""
    Write-Host "🔧 Posibles soluciones:" -ForegroundColor Yellow
    Write-Host "   1. Verifica que Docker esté corriendo" -ForegroundColor White
    Write-Host "   2. Verifica conexión a internet" -ForegroundColor White
    Write-Host "   3. Limpia cache: docker system prune -af" -ForegroundColor White
    Write-Host "   4. Revisa los logs arriba para errores específicos" -ForegroundColor White
    exit 1
}

# Push de la imagen
Write-Host ""
Write-Host "📤 Subiendo imagen al registry..." -ForegroundColor Blue
docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error subiendo imagen"
    exit 1
}

# Deployment en Container Apps
Write-Host ""
Write-Host "🚀 Desplegando en Azure Container Apps..." -ForegroundColor Blue

# Verificar si Container Apps Environment existe
$envName = "educational-env"
$envExists = az containerapp env show --name $envName --resource-group $ResourceGroup --query name --output tsv 2>$null

if (!$envExists) {
    Write-Host "   📦 Creando Container Apps Environment..." -ForegroundColor Yellow
    az containerapp env create --name $envName --resource-group $ResourceGroup --location $location --output none
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Error creando Container Apps Environment"
        exit 1
    }
}

# Obtener credenciales
$registryPassword = az acr credential show --name $RegistryName --query passwords[0].value --output tsv

# Variables de entorno para producción
$envVars = @(
    "ENVIRONMENT=production",
    "PYTHONPATH=/app",
    "HOST=0.0.0.0",
    "PORT=8000",
    "WORKERS=1"
)

# Verificar si la app existe y actualizar o crear
$appExists = az containerapp show --name $AppName --resource-group $ResourceGroup --query name --output tsv 2>$null

if ($appExists) {
    Write-Host "   🔄 Actualizando Container App existente..." -ForegroundColor Yellow
    
    az containerapp update `
        --name $AppName `
        --resource-group $ResourceGroup `
        --image $imageName `
        --output none
        
} else {
    Write-Host "   🆕 Creando nueva Container App..." -ForegroundColor Yellow
    
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
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en deployment de Container App"
    exit 1
}

# Obtener URL final
Write-Host ""
Write-Host "🔍 Obteniendo URL de la aplicación..." -ForegroundColor Blue
Start-Sleep -Seconds 5  # Esperar a que se propague

$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

# Resultado final
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Tu aplicación está disponible en:" -ForegroundColor Yellow
Write-Host "   https://$appUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Endpoints principales:" -ForegroundColor Yellow
Write-Host "   • Frontend: https://$appUrl/" -ForegroundColor White
Write-Host "   • API Docs: https://$appUrl/docs" -ForegroundColor White
Write-Host "   • API JSON: https://$appUrl/openapi.json" -ForegroundColor White
Write-Host "   • Health Check: https://$appUrl/health" -ForegroundColor White
Write-Host ""
Write-Host "🛠️ Gestión:" -ForegroundColor Yellow
Write-Host "   • Ver logs: az containerapp logs show --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor White
Write-Host "   • Reiniciar: az containerapp restart --name $AppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host "   • Escalar: az containerapp update --name $AppName --resource-group $ResourceGroup --min-replicas 2 --max-replicas 10" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Capacidad actual:" -ForegroundColor Cyan
Write-Host "   • Escalado automático: 1-5 instancias" -ForegroundColor White
Write-Host "   • CPU por instancia: 1 core" -ForegroundColor White
Write-Host "   • RAM por instancia: 2GB" -ForegroundColor White
Write-Host "   • Usuarios simultáneos estimados: 100-500" -ForegroundColor White
Write-Host ""
Write-Host "🔥 Para más rendimiento:" -ForegroundColor Red
Write-Host "   az containerapp update --name $AppName --resource-group $ResourceGroup --cpu 2.0 --memory 4.0Gi --max-replicas 10" -ForegroundColor Yellow
