# Script para probar build local
param()

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PRUEBA DE BUILD LOCAL" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

Write-Host "Construyendo imagen localmente..." -ForegroundColor Blue

# Build local para testing
docker build -t educational-test:latest . --progress=plain

if ($LASTEXITCODE -eq 0) {
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ BUILD EXITOSO!" -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
    Write-Host "Para probar localmente:" -ForegroundColor Yellow
    Write-Host "docker run -p 8000:8000 educational-test:latest" -ForegroundColor White
} else {
    Write-Host "" -ForegroundColor Red
    Write-Host "❌ ERROR EN BUILD" -ForegroundColor Red
    Write-Host "Revisa los errores arriba" -ForegroundColor Red
}
