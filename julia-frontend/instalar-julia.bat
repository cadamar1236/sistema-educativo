@echo off
echo.
echo ========================================
echo    JULIA FRONTEND - INSTALACION
echo ========================================
echo.
echo Instalando dependencias de Node.js...
echo.

REM Verificar si Node.js esta instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado.
    echo Por favor instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar si npm esta instalado
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm no esta instalado.
    echo npm deberia venir con Node.js
    pause
    exit /b 1
)

echo Node.js version:
node --version
echo npm version:
npm --version
echo.

REM Limpiar cache de npm
echo Limpiando cache de npm...
npm cache clean --force

REM Eliminar node_modules si existe
if exist "node_modules" (
    echo Eliminando node_modules existente...
    rmdir /s /q "node_modules"
)

REM Eliminar package-lock.json si existe
if exist "package-lock.json" (
    echo Eliminando package-lock.json...
    del "package-lock.json"
)

echo.
echo Instalando dependencias con --legacy-peer-deps...
npm install --legacy-peer-deps

if errorlevel 1 (
    echo.
    echo ERROR: Fallo la instalacion de dependencias.
    echo Intentando con --force...
    npm install --force
    
    if errorlevel 1 (
        echo.
        echo ERROR: No se pudieron instalar las dependencias.
        echo Revisa los logs de error arriba.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo     INSTALACION COMPLETADA
echo ========================================
echo.
echo Las dependencias se instalaron correctamente.
echo.
echo Comandos disponibles:
echo   npm run dev    - Iniciar servidor de desarrollo
echo   npm run build  - Construir para produccion
echo   npm run start  - Iniciar servidor de produccion
echo.
echo Para iniciar el servidor de desarrollo ahora:
echo   npm run dev
echo.

REM Preguntar si quiere iniciar el servidor
set /p choice="¿Quieres iniciar el servidor de desarrollo ahora? (s/n): "
if /i "%choice%"=="s" (
    echo.
    echo Iniciando servidor de desarrollo...
    npm run dev
) else (
    echo.
    echo Usa 'npm run dev' para iniciar el servidor cuando estes listo.
    echo.
)

pause
