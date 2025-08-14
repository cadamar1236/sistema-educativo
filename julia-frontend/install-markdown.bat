@echo off
echo 🚀 Instalando dependencias para renderizado de markdown bonito...
echo.

:: Instalar dependencias principales de markdown
npm install react-markdown remark-gfm remark-math rehype-katex katex

echo.
echo ✅ Verificando instalación...

:: Verificar que las dependencias están instaladas
npm list react-markdown >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ react-markdown: Instalado
) else (
    echo   ❌ react-markdown: NO instalado
)

npm list remark-gfm >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ remark-gfm: Instalado
) else (
    echo   ❌ remark-gfm: NO instalado
)

npm list remark-math >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ remark-math: Instalado
) else (
    echo   ❌ remark-math: NO instalado
)

npm list rehype-katex >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ rehype-katex: Instalado
) else (
    echo   ❌ rehype-katex: NO instalado
)

npm list katex >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ katex: Instalado
) else (
    echo   ❌ katex: NO instalado
)

echo.
echo 🎉 ¡Instalación completada!
echo.
echo 📋 Archivos creados:
echo   ✅ components/AgentResponseRenderer.tsx
echo   ✅ components/ChatInterface.tsx
echo   ✅ components/MultiAgentChat.tsx
echo   ✅ components/AICoachEnhanced.tsx
echo   ✅ components/MainApp.tsx
echo   ✅ hooks/useAgentChat.ts
echo   ✅ lib/agentService.ts
echo   ✅ styles/markdown.css
echo   ✅ app/agent-chat/page.tsx
echo   ✅ app/markdown-chat/page.tsx
echo.
echo 🚀 Para usar el sistema:
echo   1. Ejecuta: npm run dev
echo   2. Visita: http://localhost:3000/markdown-chat
echo   3. ¡Disfruta del markdown renderizado bonito!
echo.
echo 💡 URLs disponibles:
echo   - http://localhost:3000/markdown-chat (App principal)
echo   - http://localhost:3000/agent-chat (Demo completo)
echo.
pause
