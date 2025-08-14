@echo off
echo.
echo ========================================
echo    JULIA FRONTEND - SERVIDOR DEV
echo ========================================
echo.

REM Verificar si node_modules existe
if not exist "node_modules" (
    echo ERROR: node_modules no encontrado.
    echo Ejecuta 'instalar-julia.bat' primero para instalar dependencias.
    echo.
    pause
    exit /b 1
)

REM Verificar puerto 3000
echo Verificando disponibilidad del puerto 3000...
netstat -an | find "3000" >nul
if not errorlevel 1 (
    echo.
    echo ADVERTENCIA: El puerto 3000 parece estar en uso.
    echo Si tienes otro servidor Next.js corriendo, cierralo primero.
    echo.
    set /p choice="¿Continuar de todas formas? (s/n): "
    if /i not "%choice%"=="s" (
        echo Cancelado por el usuario.
        pause
        exit /b 0
    )
)

echo.
echo Iniciando servidor de desarrollo de Julia...
echo.
echo URL del servidor: http://localhost:3000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

REM Iniciar servidor de desarrollo
npm run dev

echo.
echo Servidor detenido.
pause
