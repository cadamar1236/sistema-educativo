#!/usr/bin/env python3
"""
Script de inicio para el servidor con configuración de OAuth
"""

import os
import sys
import subprocess
from pathlib import Path

def check_oauth_config():
    """Verificar que la configuración de OAuth esté completa"""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    if not client_id or not client_secret:
        print("⚠️  ADVERTENCIA: Google OAuth no está completamente configurado")
        print("   Ejecuta: python configure_oauth.py")
    else:
        print("✅ Google OAuth configurado")
        print(f"   Redirect URI: {redirect_uri}")
    
    return bool(client_id and client_secret)

def setup_environment():
    """Configurar las variables de entorno"""
    # Asegurar que las variables de entorno estén disponibles
    env_file = Path('.env')
    if env_file.exists():
        print("📁 Cargando variables de entorno desde .env")
        # Cargar manualmente las variables
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def start_server():
    """Iniciar el servidor con la configuración correcta"""
    setup_environment()
    
    # Verificar configuración OAuth
    check_oauth_config()
    
    # Configurar el puerto
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Actualizar el redirect URI si es necesario
    current_redirect = os.getenv('GOOGLE_REDIRECT_URI')
    if not current_redirect:
        os.environ['GOOGLE_REDIRECT_URI'] = f"http://localhost:{port}/auth/callback"
        print(f"🔄 Usando redirect URI por defecto: http://localhost:{port}/auth/callback")
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    
    # Importar y ejecutar uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "src.main_simple:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn no está instalado. Ejecuta: pip install uvicorn")
        sys.exit(1)

if __name__ == "__main__":
    start_server()