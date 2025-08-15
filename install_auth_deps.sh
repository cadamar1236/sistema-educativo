#!/bin/bash

echo "🚀 Instalando dependencias para autenticación y suscripciones"
echo "============================================================"

# Instalar dependencias de Python
echo "📦 Instalando dependencias de Python..."
pip install -r requirements_auth.txt

# Verificar instalación
echo ""
echo "✅ Verificando instalaciones..."
python -c "import httpx; print('✓ httpx instalado')" 2>/dev/null || echo "✗ httpx no instalado"
python -c "import jwt; print('✓ PyJWT instalado')" 2>/dev/null || echo "✗ PyJWT no instalado"
python -c "import stripe; print('✓ Stripe instalado')" 2>/dev/null || echo "✗ Stripe no instalado"
python -c "import azure.search.documents; print('✓ Azure Search instalado')" 2>/dev/null || echo "✗ Azure Search no instalado (usando fallback local)"

echo ""
echo "📝 Configuración requerida:"
echo "1. Copia .env.example a .env y completa las variables"
echo "2. Configura Google OAuth en https://console.cloud.google.com/"
echo "3. Configura Stripe en https://dashboard.stripe.com/"
echo "4. (Opcional) Configura Azure Search o usa almacenamiento local"

echo ""
echo "✅ Instalación completada!"