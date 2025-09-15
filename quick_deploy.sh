#!/bin/bash

# Script para desplegar cambios rápidamente a Azure Container Apps

echo "🚀 Desplegando cambios al sistema educativo..."

# 1. Commit de cambios
echo "📝 Haciendo commit de cambios..."
git add .
git commit -m "feat: agregar endpoint /api/agents/status para diagnóstico de agentes

- Añadido endpoint /api/agents/status que muestra:
  - Estado de agentes (disponibles/simulado)
  - Error de inicialización si existe
  - Presencia de GROQ_API_KEY
  - Modelo configurado
  - Recomendaciones para activar agentes reales
- Improved logging para container environments
- Facilita debugging en Azure Container Apps"

# 2. Push al repositorio
echo "⬆️ Subiendo cambios al repositorio..."
git push origin main

echo "✅ Cambios subidos al repositorio"
echo ""
echo "🔄 Azure Container Apps detectará los cambios y desplegará automáticamente"
echo "⏰ El despliegue toma aprox. 3-5 minutos"
echo ""
echo "🧪 Para verificar el despliegue:"
echo "   GET https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io/api/agents/status"
echo ""
echo "📋 Si los agentes siguen en modo simulado, revisa:"
echo "   1. Secreto GROQ_API_KEY en Azure Container Apps"
echo "   2. Logs del contenedor para errores de import"
echo "   3. Dependencias instaladas en el contenedor"
