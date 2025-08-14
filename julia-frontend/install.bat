@echo off
echo Instalando Julia Frontend...
echo.

npm cache clean --force
if exist "node_modules" rmdir /s /q "node_modules"
if exist "package-lock.json" del "package-lock.json"

echo Instalando dependencias...
npm install --legacy-peer-deps

if errorlevel 1 (
    echo Error. Intentando con --force...
    npm install --force
)

echo.
echo Instalacion completa. Usa: npm run dev
pause
