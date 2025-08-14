#!/bin/bash

echo "🚀 Instalando dependencias para renderizado de markdown bonito..."

# Instalar dependencias principales de markdown
npm install react-markdown remark-gfm remark-math rehype-katex katex

# Verificar que las dependencias están instaladas
echo "✅ Verificando instalación..."

# Verificar react-markdown
if npm list react-markdown >/dev/null 2>&1; then
    echo "  ✅ react-markdown: Instalado"
else
    echo "  ❌ react-markdown: NO instalado"
fi

# Verificar remark-gfm
if npm list remark-gfm >/dev/null 2>&1; then
    echo "  ✅ remark-gfm: Instalado"
else
    echo "  ❌ remark-gfm: NO instalado"
fi

# Verificar remark-math
if npm list remark-math >/dev/null 2>&1; then
    echo "  ✅ remark-math: Instalado"
else
    echo "  ❌ remark-math: NO instalado"
fi

# Verificar rehype-katex
if npm list rehype-katex >/dev/null 2>&1; then
    echo "  ✅ rehype-katex: Instalado"
else
    echo "  ❌ rehype-katex: NO instalado"
fi

# Verificar katex
if npm list katex >/dev/null 2>&1; then
    echo "  ✅ katex: Instalado"
else
    echo "  ❌ katex: NO instalado"
fi

echo ""
echo "🎉 ¡Instalación completada!"
echo ""
echo "📋 Archivos creados:"
echo "  ✅ components/AgentResponseRenderer.tsx"
echo "  ✅ components/ChatInterface.tsx"
echo "  ✅ components/MultiAgentChat.tsx"
echo "  ✅ components/AICoachEnhanced.tsx"
echo "  ✅ components/MainApp.tsx"
echo "  ✅ hooks/useAgentChat.ts"
echo "  ✅ lib/agentService.ts"
echo "  ✅ styles/markdown.css"
echo "  ✅ app/agent-chat/page.tsx"
echo "  ✅ app/markdown-chat/page.tsx"
echo ""
echo "🚀 Para usar el sistema:"
echo "  1. Ejecuta: npm run dev"
echo "  2. Visita: http://localhost:3000/markdown-chat"
echo "  3. ¡Disfruta del markdown renderizado bonito!"
echo ""
echo "💡 URLs disponibles:"
echo "  - http://localhost:3000/markdown-chat (App principal)"
echo "  - http://localhost:3000/agent-chat (Demo completo)"
echo ""
