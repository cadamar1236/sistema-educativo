"""
Configuración dinámica de OAuth para diferentes entornos
"""

import os
from typing import Optional

class OAuthConfig:
    """Clase para manejar la configuración de OAuth según el entorno"""
    
    def __init__(self):
        self.env = os.getenv('ENVIRONMENT', 'development')
        self.is_production = self.env.lower() == 'production'
        
    @property
    def google_client_id(self) -> str:
        return os.getenv('GOOGLE_CLIENT_ID', '')
    
    @property
    def google_client_secret(self) -> str:
        return os.getenv('GOOGLE_CLIENT_SECRET', '')
    
    def get_redirect_uri(self, request=None) -> str:
        """
        Obtener el redirect URI correcto según el entorno
        """
        # Si hay un request, intentar usar el host actual
        if request:
            scheme = request.url.scheme
            host = request.headers.get('x-forwarded-host') or request.url.hostname
            port = request.url.port
            
            # Para producción, usar HTTPS
            if self.is_production:
                scheme = 'https'
                host = os.getenv('PRODUCTION_HOST', 'tudominio.com')
            
            # Construir la URL base
            base_url = f"{scheme}://{host}"
            if port and port not in (80, 443):
                base_url += f":{port}"
            
            return f"{base_url}/auth/callback"
        
        # Fallback a variables de entorno
        if self.is_production:
            return os.getenv('GOOGLE_REDIRECT_URI_PROD', 'https://tudominio.com/auth/callback')
        else:
            return os.getenv('GOOGLE_REDIRECT_URI_DEV', 'http://localhost:8000/auth/callback')
    
    def get_allowed_redirect_uris(self) -> list:
        """
        Obtener la lista de URIs permitidas para Google Console
        """
        return [
            # Desarrollo
            "http://localhost:8000/auth/callback",
            "http://localhost:3000/auth/callback",
            "http://127.0.0.1:8000/auth/callback",
            "http://localhost:8001/auth/callback",
            
            # Producción (actualizar con tu dominio real)
            "https://tudominio.com/auth/callback",
            "https://www.tudominio.com/auth/callback",
            "https://api.tudominio.com/auth/callback",
            
            # Backend callback
            "http://localhost:8000/api/auth/google/callback/redirect",
            "https://tudominio.com/api/auth/google/callback/redirect",
        ]
    
    def get_frontend_url(self, request=None) -> str:
        """
        Obtener la URL del frontend según el entorno
        """
        if request:
            scheme = request.url.scheme
            host = request.headers.get('x-forwarded-host') or request.url.hostname
            
            if self.is_production:
                return f"https://{os.getenv('PRODUCTION_HOST', 'tudominio.com')}"
            else:
                return f"{scheme}://{host}:3000"
        
        return os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Instancia global
config = OAuthConfig()