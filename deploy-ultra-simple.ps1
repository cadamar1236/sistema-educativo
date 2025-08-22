# Script ultra-simple para deployment
param(
    [string]$AppName = "educational-api",
    [string]$RegistryName = "eduacr9303"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT ULTRA SIMPLE - SIN FRONTEND" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan

# Detectar configuración
$ResourceGroup = az acr show --name $RegistryName --query resourceGroup --output tsv 2>$null
if (!$ResourceGroup) {
    Write-Error "Registry $RegistryName no encontrado"
    exit 1
}

Write-Host "Usando:" -ForegroundColor Yellow
Write-Host "- Registry: $RegistryName" -ForegroundColor White
Write-Host "- Resource Group: $ResourceGroup" -ForegroundColor White

# Login al registry
az acr login --name $RegistryName

# Build imagen ultra simple
$imageName = "$RegistryName.azurecr.io/$AppName`:v$(Get-Date -Format 'yyyyMMdd-HHmm')"

Write-Host "Construyendo imagen: $imageName" -ForegroundColor Blue

# Usar Dockerfile.simple-fixed
docker build -f Dockerfile.simple-fixed -t $imageName . --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error en docker build"
    exit 1
}

# Push
Write-Host "Subiendo imagen..." -ForegroundColor Blue
docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error en docker push"  
    exit 1
}

# Update container app
Write-Host "Actualizando Container App..." -ForegroundColor Blue

az containerapp update `
    --name $AppName `
    --resource-group $ResourceGroup `
    --image $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error actualizando Container App"
    exit 1
}

# Obtener URL
$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT EXITOSO!" -ForegroundColor Green  
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URL: https://$appUrl" -ForegroundColor Cyan
Write-Host "📚 API Docs: https://$appUrl/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Ver logs:" -ForegroundColor Yellow
Write-Host "az containerapp logs show --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor White
