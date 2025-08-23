# Script de deployment SOLO BACKEND (rápido)
param(
    [string]$AppName = "educational-api",
    [string]$RegistryName = "eduacr9303"
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT SOLO BACKEND" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

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

# Login al registry
Write-Host ""
Write-Host "Conectando al registry..." -ForegroundColor Blue
az acr login --name $RegistryName

# Build imagen solo backend
$timestamp = Get-Date -Format "yyyyMMdd-HHmm"
$imageName = "$RegistryName.azurecr.io/$AppName`:backend-$timestamp"

Write-Host ""
Write-Host "🚀 Construyendo imagen BACKEND: $imageName" -ForegroundColor Blue

docker build -f Dockerfile.backend-only -t $imageName . --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en docker build"
    exit 1
}

# Push imagen
Write-Host ""
Write-Host "📤 Subiendo imagen..." -ForegroundColor Blue
docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en docker push"
    exit 1
}

# Update container app
Write-Host ""
Write-Host "🔄 Actualizando Container App..." -ForegroundColor Blue

az containerapp update `
    --name $AppName `
    --resource-group $ResourceGroup `
    --image $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error actualizando Container App"
    exit 1
}

# Obtener URL
Write-Host ""
Write-Host "🔍 Obteniendo URL..." -ForegroundColor Blue
$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

# Resultado final
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ BACKEND DESPLEGADO!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Tu API está disponible en:" -ForegroundColor Yellow
Write-Host "   https://$appUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Endpoints importantes:" -ForegroundColor Yellow
Write-Host "   • Página principal: https://$appUrl/" -ForegroundColor White
Write-Host "   • API Docs: https://$appUrl/docs" -ForegroundColor White  
Write-Host "   • Health Check: https://$appUrl/health" -ForegroundColor White
Write-Host "   • Lista de agentes: https://$appUrl/api/agents" -ForegroundColor White
Write-Host ""
Write-Host "🎉 ¡El backend está funcionando!" -ForegroundColor Green
Write-Host "   Frontend se agregará después" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Ver logs:" -ForegroundColor Yellow
Write-Host "   az containerapp logs show --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor White
