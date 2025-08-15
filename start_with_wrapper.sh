#!/bin/bash
# Startup script for the educational library system with wrapper

echo "🚀 Starting Educational Library System with Unified Wrapper"
echo "============================================================"

# Set environment variables (you'll need to add your actual API keys)
export GROQ_API_KEY="${GROQ_API_KEY:-your_groq_api_key_here}"
export PORT="${PORT:-8000}"

# Check if PM2 is available
if command -v pm2 &> /dev/null; then
    echo "✅ PM2 encontrado, iniciando con PM2..."
    
    # Stop any existing instance
    pm2 stop library-app 2>/dev/null || true
    pm2 delete library-app 2>/dev/null || true
    
    # Start the application with PM2
    pm2 start src/main_simple.py \
        --name "library-app" \
        --interpreter python3 \
        --watch false \
        --autorestart true \
        --max-memory-restart 1G \
        -- --host 0.0.0.0 --port $PORT
    
    # Show status
    pm2 status
    echo ""
    echo "✅ Aplicación iniciada con PM2"
    echo "📊 Ver logs: pm2 logs library-app --nostream"
    echo "🔄 Reiniciar: pm2 restart library-app"
    echo "🛑 Detener: pm2 stop library-app"
else
    echo "⚠️ PM2 no encontrado, iniciando directamente..."
    
    # Start directly with uvicorn
    cd /home/user/webapp
    python3 -m uvicorn src.main_simple:app \
        --host 0.0.0.0 \
        --port $PORT \
        --reload \
        &
    
    echo "✅ Aplicación iniciada en puerto $PORT"
fi

echo ""
echo "🌐 La aplicación está disponible en:"
echo "   - Local: http://localhost:$PORT"
echo "   - API Docs: http://localhost:$PORT/docs"
echo ""
echo "📚 Características del wrapper unificado:"
echo "   ✅ Maneja automáticamente diferencias de parámetros"
echo "   ✅ Soporta Educational RAG Agent (cuando está disponible)"
echo "   ✅ Fallback a servicio mejorado con OCR"
echo "   ✅ Soporte para 20+ tipos de archivos"
echo "   ✅ Procesamiento de imágenes con OCR"
echo ""