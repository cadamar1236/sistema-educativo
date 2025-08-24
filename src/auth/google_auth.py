"""
Sistema de autenticación con Google OAuth 2.0
"""

import os
import jwt
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
import hashlib
from .users_db import get_or_create_from_google

logger = logging.getLogger(__name__)

# Configuración
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
TEACHER_EMAILS = {
    e.strip().lower() for e in os.getenv("TEACHER_EMAILS", "").split(",") if e.strip()
}

# URLs de Google OAuth
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# Security
security = HTTPBearer()

class GoogleUser(BaseModel):
    """Modelo de usuario de Google"""
    id: str
    email: str
    name: str
    picture: str
    verified_email: bool
    locale: Optional[str] = None

class AuthToken(BaseModel):
    """Token de autenticación"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRATION_HOURS * 3600
    refresh_token: Optional[str] = None
    user: Dict[str, Any]

class GoogleAuthService:
    """Servicio de autenticación con Google"""
    
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ Google OAuth no configurado correctamente")
    
    def get_authorization_url(self, state: str = None, redirect_override: Optional[str] = None) -> str:
        """Obtener URL de autorización de Google.
        redirect_override permite forzar un redirect_uri dinámico (ej: dominio productivo) sin mutar estado global."""
        if not state:
            state = secrets.token_urlsafe(32)

        redirect_uri = redirect_override or self.redirect_uri
        if redirect_override and redirect_override != self.redirect_uri:
            # Log informativo para depurar diferencias de entorno
            logger.info(f"🔄 Usando redirect_uri dinámico (override) {redirect_override} (base default: {self.redirect_uri})")

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "consent"
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{GOOGLE_AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_override: Optional[str] = None) -> Dict[str, Any]:
        """Intercambiar código de autorización por token.
        redirect_override permite usar el mismo override utilizado al generar la URL de autorización."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_override or self.redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code != 200:
                # Log detallado para depuración (NO incluye secrets)
                safe_payload = {
                    "status": response.status_code,
                    "redirect_uri_used": redirect_override or self.redirect_uri,
                    "has_client_id": bool(self.client_id),
                    "error_body": None
                }
                try:
                    safe_payload["error_body"] = response.json()
                except Exception:
                    safe_payload["error_body"] = response.text[:500]
                logger.error(f"Google OAuth token exchange failed: {safe_payload}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error obteniendo token de Google"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> GoogleUser:
        """Obtener información del usuario de Google"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Error obteniendo información del usuario"
                )
            
            user_data = response.json()
            return GoogleUser(**user_data)
    
    def create_jwt_token(self, user: GoogleUser, subscription_tier: str = "free", role: str = "student") -> str:
        """Crear JWT token para el usuario con rol"""
        payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "subscription_tier": subscription_tier,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verificar y decodificar JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    
    async def authenticate_with_google(self, code: str, redirect_override: Optional[str] = None) -> AuthToken:
        """Proceso completo de autenticación con Google"""
        token_data = await self.exchange_code_for_token(code, redirect_override=redirect_override)
        
        # 2. Obtener información del usuario
        google_user = await self.get_user_info(token_data["access_token"])
        # 3. Determinar rol (simple: lista blanca de correos de profesores)
        role = "teacher" if google_user.email.lower() in TEACHER_EMAILS else "student"
        
        # 4. Obtener tier de suscripción (conectar con Stripe)
        subscription_tier = await self.get_user_subscription_tier(google_user.id)
        
        # 5. Persistir / actualizar usuario en BD
        db_user = get_or_create_from_google({
            "id": google_user.id,
            "email": google_user.email,
            "name": google_user.name,
            "picture": google_user.picture
        }, role, subscription_tier)

        # 6. Crear JWT token (fuente de verdad: BD)
        jwt_token = self.create_jwt_token(google_user, db_user.subscription_tier, db_user.role)
        
        return AuthToken(
            access_token=jwt_token,
            refresh_token=token_data.get("refresh_token"),
            user={
                "id": google_user.id,
                "email": google_user.email,
                "name": google_user.name,
                "picture": google_user.picture,
                "subscription_tier": db_user.subscription_tier,
                "role": db_user.role
            }
        )
    
    async def get_user_subscription_tier(self, user_id: str) -> str:
        """Obtener el tier de suscripción del usuario (se conectará con Stripe)"""
        # Por ahora retornamos "free", esto se conectará con Stripe
        return "free"

# Dependencia para verificar autenticación
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Obtener usuario actual desde el token"""
    auth_service = GoogleAuthService()
    token = credentials.credentials
    
    try:
        payload = auth_service.verify_jwt_token(token)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Dependencia para verificar suscripción
async def require_subscription(
    tier: str = "free",
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verificar que el usuario tiene el tier de suscripción requerido"""
    user_tier = current_user.get("subscription_tier", "free")
    
    tier_levels = {
        "free": 0,
        "basic": 1,
        "pro": 2,
        "enterprise": 3
    }
    
    if tier_levels.get(user_tier, 0) < tier_levels.get(tier, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Se requiere suscripción {tier} o superior"
        )
    
    return current_user

# ====== ROLES ======
async def require_teacher(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Verificar que el usuario es profesor"""
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Acceso solo para profesores")
    return current_user

def role_required(*roles: str):
    """Generar dependencia para uno o varios roles"""
    async def _checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Rol no autorizado")
        return current_user
    return _checker

# Instancia global
google_auth = GoogleAuthService()