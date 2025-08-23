<#
Automatiza la construcción del frontend (Next.js export) y lo embebe dentro del backend.
Uso (PowerShell):
  ./scripts/build_frontend_and_embed.ps1 [-FrontendPath julia-frontend] [-StaticTarget static]
Requisitos:
  - Node y npm instalados
  - package.json con script build que genere out/ (output:'export')
#>
param(
  [string]$FrontendPath = 'julia-frontend',
  [string]$StaticTarget = 'static'
)

$ErrorActionPreference = 'Stop'
Write-Host '==> 1. Verificando carpeta frontend' -ForegroundColor Cyan
if (-not (Test-Path $FrontendPath)) { throw "No existe carpeta $FrontendPath" }

Push-Location $FrontendPath
try {
  Write-Host '==> 2. Instalando dependencias (npm ci si existe package-lock.json)...' -ForegroundColor Cyan
  if (Test-Path 'package-lock.json') { npm ci } else { npm install }

  Write-Host '==> 3. Limpiando build previo' -ForegroundColor Cyan
  if (Test-Path '.next') { Remove-Item -Recurse -Force '.next' }
  if (Test-Path 'out') { Remove-Item -Recurse -Force 'out' }

  Write-Host '==> 4. Ejecutando build (export estático)' -ForegroundColor Cyan
  npm run build
  if (-not (Test-Path 'out')) { throw 'No se generó la carpeta out (revisa next.config.js output: export)' }
}
finally {
  Pop-Location
}

Write-Host '==> 5. Preparando carpeta destino backend' -ForegroundColor Cyan
if (-not (Test-Path $StaticTarget)) { New-Item -ItemType Directory -Path $StaticTarget | Out-Null }

# Limpiar solamente contenido generado previamente (no tocar uploads u otros subdirectorios de datos)
Get-ChildItem $StaticTarget | Where-Object { $_.Name -notin @('uploads','data') } | ForEach-Object {
  Remove-Item -Recurse -Force $_.FullName
}

Write-Host '==> 6. Copiando export (out/*) ->' $StaticTarget -ForegroundColor Cyan
$exportDir = Join-Path $FrontendPath 'out'
if (-not (Test-Path $exportDir)) { throw "No existe carpeta $exportDir" }
# Copiar contenido interno (no la carpeta out en sí)
Get-ChildItem -LiteralPath $exportDir | ForEach-Object {
  Copy-Item -Recurse -Force -Path $_.FullName -Destination $StaticTarget
}

Write-Host '==> 7. Verificando archivos clave' -ForegroundColor Cyan
$indexFile = Join-Path $StaticTarget 'index.html'
if (-not (Test-Path $indexFile)) { throw 'Falta index.html en static/' }
if (-not (Test-Path (Join-Path $StaticTarget '_next'))) { throw 'Falta carpeta _next (assets Next.js)' }

Write-Host '==> 8. Generando archivo de versión para cache busting' -ForegroundColor Cyan
$versionToken = (Get-Date).ToString('yyyyMMddHHmmss') + '-' + ([System.Guid]::NewGuid().ToString().Substring(0,8))
$versionFile = Join-Path $StaticTarget "build-version.txt"
Set-Content -Path $versionFile -Value $versionToken -Encoding UTF8
Write-Host "    -> build-version.txt creado con token $versionToken" -ForegroundColor DarkGray

<#
Explicación:
- Algunos navegadores pueden estar sirviendo chunks viejos en cache y reciben index.html (fallback) -> 'Unexpected token <'.
- Este archivo de versión permite verificar rápidamente si el frontend que ves es el recién construido (abre /static/build-version.txt en el navegador o curl).
- Si sigues viendo errores de chunks, fuerza un hard reload (Ctrl+F5) o limpia Application Storage / Cache Storage en las DevTools.
-> Opcional: Puedes añadir un header de no-cache en Nginx para /index.html y dejar cache agresivo solo para /_next/static.
#>

Write-Host '==> 9. Listo. Ejecuta ahora (desarrollo local):' -ForegroundColor Green
Write-Host '    python -m uvicorn src.main_simple:app --reload' -ForegroundColor Yellow

Write-Host 'TIP: Abre http://localhost:8000/build-version.txt para confirmar que ves el token reciente.' -ForegroundColor DarkCyan
