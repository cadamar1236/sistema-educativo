# Script de deployment con frontend corregido
param(
    [string]$AppName = "educational-api",
    [string]$RegistryName = "eduacr9303"
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT FULLSTACK - FRONTEND FIXED" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Detectar configuración
$ResourceGroup = az acr show --name $RegistryName --query resourceGroup --output tsv 2>$null
if (!$ResourceGroup) {
    Write-Error "Registry $RegistryName no encontrado"
    exit 1
}

Write-Host "Configuración:" -ForegroundColor Green
Write-Host "- App: $AppName" -ForegroundColor White
Write-Host "- Registry: $RegistryName" -ForegroundColor White  
Write-Host "- Resource Group: $ResourceGroup" -ForegroundColor White

# Verificar estructura
$hasBackend = Test-Path "src/main_simple.py"
$hasFrontend = Test-Path "julia-frontend/package.json"
$hasRequirements = Test-Path "requirements.txt"

Write-Host ""
Write-Host "Verificación de archivos:" -ForegroundColor Blue
Write-Host "✅ Backend (main_simple.py): $hasBackend" -ForegroundColor $(if($hasBackend){"Green"}else{"Red"})
Write-Host "✅ Frontend (Next.js): $hasFrontend" -ForegroundColor $(if($hasFrontend){"Green"}else{"Red"})  
Write-Host "✅ Requirements: $hasRequirements" -ForegroundColor $(if($hasRequirements){"Green"}else{"Red"})

if (!$hasBackend -or !$hasRequirements) {
    Write-Error "Faltan archivos esenciales"
    exit 1
}

# Login al registry
Write-Host ""
Write-Host "Conectando al registry..." -ForegroundColor Blue
az acr login --name $RegistryName

# Build con timestamp para cache busting
$timestamp = Get-Date -Format "yyyyMMdd-HHmm"
$imageName = "$RegistryName.azurecr.io/$AppName`:$timestamp"

Write-Host ""
Write-Host "Construyendo imagen: $imageName" -ForegroundColor Blue

# Usar Dockerfile.frontend-fixed
docker build -f Dockerfile.frontend-fixed -t $imageName . --no-cache --progress=plain

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en docker build"
    Write-Host ""
    Write-Host "🔧 Soluciones posibles:" -ForegroundColor Yellow
    Write-Host "1. Verificar que Docker esté corriendo" -ForegroundColor White
    Write-Host "2. Verificar conexión a internet" -ForegroundColor White
    Write-Host "3. Limpiar cache: docker system prune -f" -ForegroundColor White
    exit 1
}

# Push imagen
Write-Host ""
Write-Host "Subiendo imagen..." -ForegroundColor Blue
docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en docker push"
    exit 1
}

# Update container app
Write-Host ""
Write-Host "Actualizando Container App..." -ForegroundColor Blue

az containerapp update `
    --name $AppName `
    --resource-group $ResourceGroup `
    --image $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error actualizando Container App"
    
    # Intentar crear si no existe
    Write-Host ""
    Write-Host "Intentando crear Container App nueva..." -ForegroundColor Yellow
    
    $envName = "educational-env"
    $registryPassword = az acr credential show --name $RegistryName --query passwords[0].value --output tsv
    $registryServer = "$RegistryName.azurecr.io"
    
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
        --env-vars "ENVIRONMENT=production" "PYTHONPATH=/app" "PORT=8000" "HOST=0.0.0.0"
        
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Error creando Container App"
        exit 1
    }
}

# Obtener URL
Write-Host ""
Write-Host "Obteniendo URL..." -ForegroundColor Blue
$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

# Resultado final
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "🎉 DEPLOYMENT EXITOSO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Tu aplicación está disponible en:" -ForegroundColor Yellow
Write-Host "   https://$appUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Endpoints principales:" -ForegroundColor Yellow
Write-Host "   • Frontend: https://$appUrl/" -ForegroundColor White
Write-Host "   • API Docs: https://$appUrl/docs" -ForegroundColor White
Write-Host "   • Health: https://$appUrl/health" -ForegroundColor White
Write-Host ""
Write-Host "🛠️ Comandos útiles:" -ForegroundColor Yellow
Write-Host "   • Ver logs: az containerapp logs show --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor White
Write-Host "   • Reiniciar: az containerapp restart --name $AppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Capacidad actual:" -ForegroundColor Cyan
Write-Host "   • 1-5 instancias con auto-escalado" -ForegroundColor White
Write-Host "   • ~100-300 usuarios simultáneos" -ForegroundColor White
Write-Host "   • CPU: 1 core, RAM: 2GB por instancia" -ForegroundColor White
