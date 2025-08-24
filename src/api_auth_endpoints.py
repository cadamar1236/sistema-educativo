"""
Endpoints de autenticación con Google y suscripciones con Stripe
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, Any, Optional
import hmac, hashlib, base64, json, time
import logging
import os
from datetime import datetime

# Importar servicios
try:
    from src.auth.google_auth import google_auth, get_current_user, require_subscription, require_teacher
except ImportError:  # fallback if executed with package root already at src
    from auth.google_auth import google_auth, get_current_user, require_subscription, require_teacher
from auth.users_db import update_role
from payments.stripe_subscription import stripe_service, SubscriptionTier

logger = logging.getLogger(__name__)

# Crear router
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
subscription_router = APIRouter(prefix="/api/subscription", tags=["Subscriptions"])

# Router adicional para capturar redirecciones de OAuth que lleguen sin el prefijo /api
oauth_redirect_router = APIRouter(prefix="/auth", tags=["OAuth Redirects"])

# ==================== ENDPOINTS DE AUTENTICACIÓN ====================

STATE_MAX_AGE = 1800  # 30 minutos para dar más tiempo

def _oauth_state_secret() -> bytes:
    return (getattr(google_auth, 'JWT_SECRET', None) or os.getenv('JWT_SECRET', 'dev_secret')).encode()

def _sign_state(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(',', ':')).encode()
    b64 = base64.urlsafe_b64encode(raw).decode().rstrip('=')
    sig = hmac.new(_oauth_state_secret(), b64.encode(), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"

def _parse_state(state: Optional[str]) -> Optional[Dict[str, Any]]:
    if not state or '.' not in state:
        return None
    try:
        b64, sig = state.split('.', 1)
        expected = hmac.new(_oauth_state_secret(), b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            logger.warning("STATE firma inválida")
            return None
        data = base64.urlsafe_b64decode(b64 + '==')
        payload = json.loads(data.decode())
        if int(time.time()) - int(payload.get('t', 0)) > STATE_MAX_AGE:
            logger.warning("STATE expirado")
            return None
        return payload
    except Exception as e:
        logger.warning(f"Error parseando state: {e}")
        return None

@auth_router.get("/google/login")
async def google_login(
    request: Request,
    next: str = "/dashboard",
    force_http_loopback: bool = True,
    prefer_localhost: bool = True
):
    """Login unificado Google: siempre usa callback backend /api/auth/google/callback/redirect.
    Devuelve auth_url y state firmado que incluye redirect y next interno."""
    try:
        public_base = os.getenv("PUBLIC_BASE_URL")  # ej: https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io
        if public_base:
            # Normalizar sin slash final
            public_base = public_base.rstrip('/')
            from urllib.parse import urlparse
            pu = urlparse(public_base)
            proto = pu.scheme or 'https'
            host = pu.netloc
        else:
            # Cabeceras en orden de preferencia
            raw_host = (request.headers.get("x-forwarded-host") or
                        request.headers.get("x-original-host") or
                        request.headers.get("host") or
                        request.url.hostname or "")
            proto = request.headers.get("x-forwarded-proto") or request.url.scheme or 'https'
            port = request.url.port
            # Solo forzar localhost en loopback genuino (no en producción)
            if prefer_localhost and raw_host.startswith("127."):
                raw_host = "localhost"
            # No forzar http si tenemos dominio público (contiene un punto y no es localhost)
            if force_http_loopback and (raw_host.startswith("localhost") or raw_host.startswith("127.")) and '.' not in raw_host:
                proto = "http"
            if ':' not in raw_host and port and port not in (80, 443):
                host = f"{raw_host}:{port}"
            else:
                host = raw_host
        # Usar el redirect URI estándar que está registrado en Google OAuth
        base_redirect = f"{proto}://{host}/auth/callback"
        safe_next = next if isinstance(next, str) and next.startswith('/') else '/dashboard'
        signed_state = _sign_state({"r": base_redirect, "n": safe_next, "t": int(time.time())})
        auth_url = google_auth.get_authorization_url(state=signed_state, redirect_override=base_redirect)
        logger.info(f"[oauth] login host={host} redirect={base_redirect} next={safe_next} public_base={'yes' if public_base else 'no'}")
        return {"auth_url": auth_url, "redirect_uri_used": base_redirect, "state": signed_state}
    except Exception as e:
        logger.error(f"Error iniciando login con Google: {e}")
        raise HTTPException(status_code=500, detail="Error iniciando autenticación")

def _derive_effective_redirect(request: Request, redirect_uri: Optional[str]) -> Optional[str]:
    """Derivar redirect_uri coherente con el host actual si no se pasó explícita."""
    if redirect_uri:
        return redirect_uri
    # Host + puerto real
    raw_host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
    port = request.url.port
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    # Si es loopback forzar http para coincidir con registros típicos
    if raw_host.startswith("127.") or raw_host.startswith("localhost"):
        proto = "http"
    # Incluir puerto si no estándar y no ya presente en header
    if ':' not in raw_host and port and port not in (80, 443):
        host = f"{raw_host}:{port}"
    else:
        host = raw_host
    if not host:
        return None
    env_redirect = os.getenv("GOOGLE_REDIRECT_URI", "")
    if env_redirect and host in env_redirect:
        return env_redirect
    if env_redirect:
        try:
            from urllib.parse import urlparse
            p = urlparse(env_redirect)
            return f"{proto}://{host}{p.path}"
        except Exception:
            pass
    return f"{proto}://{host}/auth/callback"

def _normalize_redirect(r: Optional[str]) -> Optional[str]:
    if not r:
        return r
    r = r.split('?')[0].split('#')[0]
    if r.endswith('/'):
        r = r.rstrip('/')
    # Permitir tanto /auth/callback como /api/auth/google/callback/redirect sin forzar
    return r

@auth_router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: Optional[str] = None,
    redirect_uri: Optional[str] = Query(None)
):
    """Callback de Google OAuth que devuelve JSON y ahora también setea cookie del token.
    El front debe guardar access_token (Authorization: Bearer) o usar la cookie."""
    try:
        effective_redirect = _normalize_redirect(_derive_effective_redirect(request, redirect_uri))
        try:
            auth_token = await google_auth.authenticate_with_google(code, redirect_override=effective_redirect)
        except HTTPException as he:
            # Intento de fallback si es redirect_uri mismatch (mensaje típico Google)
            detail = getattr(he, 'detail', '')
            if 'redirect_uri' in str(detail).lower():
                logger.warning("Reintentando intercambio sin override por posible redirect_uri mismatch")
                auth_token = await google_auth.authenticate_with_google(code, redirect_override=None)
            else:
                raise
        payload = {
            "success": True,
            "access_token": auth_token.access_token,
            "user": auth_token.user,
            "message": "Autenticación exitosa",
            "redirect_uri_used": effective_redirect or google_auth.redirect_uri
        }
        # Construir respuesta y añadir cookie (no HttpOnly para que frontend pueda migrar si esperaba cookie)
        from datetime import timedelta
        resp = JSONResponse(payload)
        # SECURE: en producción (https) secure=True
        secure_flag = (request.url.scheme == 'https') or (request.headers.get('x-forwarded-proto') == 'https')
        resp.set_cookie(
            key="access_token",
            value=auth_token.access_token,
            max_age=int(timedelta(hours=24).total_seconds()),
            httponly=False,
            secure=secure_flag,
            samesite="Lax",
            path="/"
        )
        return resp
    except Exception as e:
        logger.error(f"Error en callback de Google: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Error en autenticación con Google (callback)")

# Remove duplicate definitions - keeping only the first set

@auth_router.get("/debug/config")
async def auth_debug_config(request: Request):
    """Diagnóstico de configuración OAuth para depurar fallos de callback."""
    host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    return {
        "host": host,
        "proto": proto,
        "env_GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI"),
        "env_PUBLIC_BASE_URL": os.getenv("PUBLIC_BASE_URL"),
        "default_service_redirect_uri": google_auth.redirect_uri,
        "suggested_frontend_callback": f"{proto}://{host}/auth/callback" if host else None,
        "suggested_backend_callback": f"{proto}://{host}/api/auth/google/callback/redirect" if host else None,
        "cookie_secure_example": (proto == 'https')
    }

@auth_router.get("/debug/token")
async def debug_token_check(request: Request):
    """Debug endpoint to check if token is being received correctly."""
    auth_header = request.headers.get("authorization", "")
    cookie_token = request.cookies.get("access_token", "")
    
    return {
        "auth_header": auth_header[:50] + "..." if auth_header else "None",
        "cookie_token": cookie_token[:50] + "..." if cookie_token else "None",
        "headers": dict(request.headers),
        "cookies": dict(request.cookies)
    }

@auth_router.get("/me")
async def get_current_user_info(request: Request):
    """Obtener información del usuario actual - con múltiples formas de autenticación"""
    token = None
    
    # 1. Intentar desde Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    # 2. Si no hay header, intentar desde cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verificar el token JWT
        payload = google_auth.verify_jwt_token(token)
        return {
            "user": {
                "id": payload["sub"],
                "email": payload["email"], 
                "name": payload["name"],
                "picture": payload.get("picture", ""),
                "subscription_tier": payload.get("subscription_tier", "free"),
                "role": payload.get("role", "student")
            },
            "subscription_tier": payload.get("subscription_tier", "free"),
            "role": payload.get("role", "student")
        }
    except Exception as e:
        logger.error(f"Error verificando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )

@auth_router.get("/debug/auth")
async def debug_auth_status(request: Request):
    """Endpoint de debug para diagnosticar problemas de autenticación"""
    debug_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_headers": dict(request.headers),
        "cookies": dict(request.cookies),
        "auth_analysis": {}
    }
    
    # Analizar Authorization header
    auth_header = request.headers.get("authorization", "")
    debug_info["auth_analysis"]["authorization_header"] = {
        "present": bool(auth_header),
        "starts_with_bearer": auth_header.startswith("Bearer "),
        "length": len(auth_header),
        "preview": auth_header[:50] + "..." if len(auth_header) > 50 else auth_header
    }
    
    # Analizar cookie
    cookie_token = request.cookies.get("access_token")
    debug_info["auth_analysis"]["cookie_token"] = {
        "present": bool(cookie_token),
        "length": len(cookie_token) if cookie_token else 0,
        "preview": cookie_token[:50] + "..." if cookie_token and len(cookie_token) > 50 else cookie_token
    }
    
    # Intentar extraer token
    token = None
    token_source = None
    
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        token_source = "authorization_header"
    elif cookie_token:
        token = cookie_token
        token_source = "cookie"
    
    debug_info["auth_analysis"]["token_extraction"] = {
        "token_found": bool(token),
        "token_source": token_source,
        "token_length": len(token) if token else 0,
        "token_preview": token[:50] + "..." if token and len(token) > 50 else token
    }
    
    # Si hay token, intentar verificarlo
    if token:
        try:
            payload = google_auth.verify_jwt_token(token)
            debug_info["auth_analysis"]["token_verification"] = {
                "status": "valid",
                "payload_keys": list(payload.keys()) if payload else [],
                "user_id": payload.get("sub", "N/A") if payload else "N/A",
                "email": payload.get("email", "N/A") if payload else "N/A",
                "exp": payload.get("exp", "N/A") if payload else "N/A"
            }
        except Exception as e:
            debug_info["auth_analysis"]["token_verification"] = {
                "status": "invalid",
                "error": str(e),
                "error_type": type(e).__name__
            }
    else:
        debug_info["auth_analysis"]["token_verification"] = {
            "status": "no_token",
            "message": "No token found to verify"
        }
    
    return debug_info

@auth_router.get("/google/callback/redirect")
async def google_callback_redirect(
    request: Request,
    code: str = Query(...),
    state: Optional[str] = None
):
    """Callback final: intercambia el code, setea cookie + storage y redirige al dashboard (o 'next' del state)."""
    try:
        payload = _parse_state(state)
        # redirect_uri exacto usado en login; si falla se intenta derivar.
        chosen_redirect = (payload or {}).get('r') or _normalize_redirect(_derive_effective_redirect(request, None))
        next_path = (payload or {}).get('n') or '/dashboard'
        if not isinstance(next_path, str) or not next_path.startswith('/'):
            next_path = '/dashboard'
        
        # Add timeout and error handling for OAuth token exchange
        try:
            auth_token = await google_auth.authenticate_with_google(code, redirect_override=chosen_redirect)
        except HTTPException as he:
            if 'redirect_uri' in str(getattr(he, 'detail', '')).lower():
                logger.warning('[oauth] retry sin override por mismatch redirect_uri')
                auth_token = await google_auth.authenticate_with_google(code, redirect_override=None)
            else:
                raise
        except Exception as e:
            logger.error(f"[OAuth] Error durante intercambio de token: {e}")
            # Return error page instead of raising exception to prevent 504
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error de Autenticación</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                        .error { color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto; }
                    </style>
                </head>
                <body>
                    <div class="error">
                        <h2>Error de Autenticación</h2>
                        <p>Hubo un problema procesando su solicitud. Por favor intente de nuevo.</p>
                        <a href="/login">Volver al Login</a>
                    </div>
                </body>
                </html>
            """, status_code=500)
        
        # Get frontend URL configuration
        public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip('/')
        frontend_url = os.getenv("FRONTEND_URL")
        
        if not frontend_url:
            if public_base:
                frontend_url = public_base
            else:
                host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
                proto = request.headers.get("x-forwarded-proto") or request.url.scheme or 'https'
                frontend_url = f"{proto}://{host}"
        
        full_redirect_url = f"{frontend_url}{next_path}"
        
        # Respuesta HTML que guarda el token y redirige
        html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Autenticando...</title></head><body>
<script>
(function() {{
  try {{
    var token = {auth_token.access_token!r};
    console.log('[Auth] Guardando token:', token.substring(0, 20) + '...');
    localStorage.setItem('access_token', token);
    sessionStorage.setItem('access_token', token);
    document.cookie = 'access_token=' + token + '; Path=/; SameSite=Lax';
    console.log('[Auth] Token guardado, redirigiendo a:', {full_redirect_url!r});
    
    // Verificar que se guardó correctamente
    var stored = localStorage.getItem('access_token');
    if (stored === token) {{
      console.log('[Auth] Token verificado en localStorage');
      setTimeout(function() {{
        window.location.replace({full_redirect_url!r});
      }}, 100);
    }} else {{
      console.error('[Auth] Error: token no se guardó correctamente');
      document.body.innerHTML = 'Error: token no se guardó correctamente';
    }}
  }} catch(e) {{
    console.error('[Auth] Error almacenando token:', e);
    document.body.innerHTML = 'Error almacenando token: ' + e;
    return;
  }}
}})();
</script>
<div>Guardando token y redirigiendo...</div>
</body></html>"""
        
        secure_flag = (request.headers.get('x-forwarded-proto') == 'https') or (request.url.scheme == 'https')
        from datetime import timedelta
        resp = HTMLResponse(html)
        resp.set_cookie(
            key="access_token",
            value=auth_token.access_token,
            max_age=int(timedelta(hours=24).total_seconds()),
            httponly=False,
            secure=secure_flag,
            samesite="Lax",
            path="/"
        )
        return resp
        
    except Exception as e:
        logger.error(f"Error en callback redirect Google: {type(e).__name__}: {e}")
        # Return error page instead of raising exception
        return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error de Autenticación</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                    .error { color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>Error de Autenticación</h2>
                    <p>Hubo un problema procesando su solicitud. Por favor intente de nuevo.</p>
                    <a href="/login">Volver al Login</a>
                </div>
            </body>
            </html>
        """, status_code=500)
# ==================== ENDPOINTS DE SUSCRIPCIÓN ====================

@subscription_router.get("/status")
async def get_subscription_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Obtener estado actual de suscripción del usuario"""
    try:
        # Aquí obtendrías el subscription_id de tu BD
        subscription_id = current_user.get("subscription_id")
        
        if not subscription_id:
            return {
                "tier": SubscriptionTier.FREE,
                "status": "active",
                "plan": stripe_service.get_plan_features(SubscriptionTier.FREE).dict()
            }
        
        subscription = await stripe_service.get_subscription(subscription_id)
        
        if subscription:
            plan = stripe_service.get_plan_features(subscription["tier"])
            return {
                "tier": subscription["tier"],
                "status": subscription["status"],
                "current_period_end": subscription["current_period_end"],
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
                "plan": plan.dict()
            }
        else:
            return {
                "tier": SubscriptionTier.FREE,
                "status": "active",
                "plan": stripe_service.get_plan_features(SubscriptionTier.FREE).dict()
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo suscripción: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo suscripción")

@subscription_router.post("/checkout")
async def create_checkout_session(
    tier: SubscriptionTier,
    billing_period: str = "monthly",  # monthly o yearly
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Crear sesión de checkout para nueva suscripción o upgrade"""
    try:
        # Obtener plan
        plan = stripe_service.plans.get(tier)
        if not plan:
            raise HTTPException(status_code=400, detail="Plan no válido")
        
        # Obtener price_id según el período de facturación
        if billing_period == "yearly":
            price_id = plan.stripe_price_id_yearly
        else:
            price_id = plan.stripe_price_id_monthly
        
        if not price_id:
            raise HTTPException(status_code=400, detail="Plan no disponible para compra")
        
        # Crear o obtener customer de Stripe
        # Aquí obtendrías el customer_id de tu BD
        customer_id = current_user.get("stripe_customer_id")
        
        if not customer_id:
            customer = await stripe_service.create_customer(
                email=current_user["email"],
                name=current_user["name"],
                metadata={"user_id": current_user["sub"]}
            )
            customer_id = customer["id"]
            # Guardar customer_id en BD
        
        # Crear sesión de checkout
        session = await stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/subscription/cancel",
            metadata={
                "user_id": current_user["sub"],
                "tier": tier.value
            }
        )
        
        return {
            "checkout_url": session["url"],
            "session_id": session["id"]
        }
        
    except Exception as e:
        logger.error(f"Error creando sesión de checkout: {e}")
        raise HTTPException(status_code=500, detail="Error creando sesión de pago")

@subscription_router.post("/cancel")
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancelar suscripción actual"""
    try:
        # Obtener subscription_id de la BD
        subscription_id = current_user.get("subscription_id")
        
        if not subscription_id:
            raise HTTPException(status_code=400, detail="No hay suscripción activa")
        
        success = await stripe_service.cancel_subscription(subscription_id, at_period_end)
        
        if success:
            return {
                "success": True,
                "message": "Suscripción cancelada" + (" al final del período" if at_period_end else " inmediatamente")
            }
        else:
            raise HTTPException(status_code=500, detail="Error cancelando suscripción")
            
    except Exception as e:
        logger.error(f"Error cancelando suscripción: {e}")
        raise HTTPException(status_code=500, detail="Error cancelando suscripción")

@subscription_router.post("/webhook")
async def stripe_webhook(request: Request):
    """Webhook de Stripe para eventos de suscripción"""
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        result = await stripe_service.handle_webhook(payload, signature)
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Error procesando webhook de Stripe: {e}")
        raise HTTPException(status_code=400, detail="Error procesando webhook")

@subscription_router.get("/usage")
async def get_usage_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Obtener estadísticas de uso del usuario"""
    try:
        # Aquí obtendrías las estadísticas reales de tu BD
        tier = SubscriptionTier(current_user.get("subscription_tier", "free"))
        plan = stripe_service.get_plan_features(tier)
        
        # Ejemplo de estadísticas (conectar con tu BD real)
        usage = {
            "documents_uploaded": {
                "current": 3,
                "limit": plan.limits.get("documents_per_month", 5),
                "percentage": 60
            },
            "queries_today": {
                "current": 7,
                "limit": plan.limits.get("queries_per_day", 10),
                "percentage": 70
            },
            "storage_used_mb": {
                "current": 45,
                "limit": plan.limits.get("storage_mb", 100),
                "percentage": 45
            }
        }
        
        return {
            "tier": tier.value,
            "usage": usage,
            "limits": plan.limits
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de uso: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")

# ==================== ENDPOINTS DE REDIRECCIÓN OAUTH ====================

@oauth_redirect_router.get("/callback")
async def oauth_callback_handler(request: Request, state: str = None, code: str = None):
    """
    Endpoint estándar para el callback de Google OAuth - /auth/callback
    Este es el endpoint que Google espera según la configuración GOOGLE_REDIRECT_URI
    """
    try:
        logger.info(f"[OAuth] Callback capturado en /auth/callback")
        logger.info(f"[OAuth] State: {state}, Code: {code[:20]}..." if code else "No code")
        
        # Procesar el callback directamente aquí
        if not state or not code:
            logger.error("[OAuth] Faltan parámetros state o code")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>Faltan parámetros requeridos para la autenticación.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)

        # Parsear y validar state
        state_data = _parse_state(state)
        if not state_data:
            logger.error("[OAuth] State inválido o expirado")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>La sesión de autenticación ha expirado.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)
        
        redirect_to = state_data.get("n", "/dashboard")
        
        # Autenticar con Google usando el redirect URI correcto
        try:
            # Use the standard /auth/callback redirect URI that Google expects
            public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip('/')
            if public_base:
                correct_redirect_uri = f"{public_base}/auth/callback"
            else:
                host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
                proto = request.headers.get("x-forwarded-proto") or request.url.scheme or 'https'
                correct_redirect_uri = f"{proto}://{host}/auth/callback"
                
            logger.info(f"[OAuth] Intentando autenticación con redirect_uri: {correct_redirect_uri}")
            auth_token = await google_auth.authenticate_with_google(code, redirect_override=correct_redirect_uri)
            
            # Generar HTML de respuesta que almacena el token y redirige al frontend
            frontend_domain = "https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io"
            user_data_json = json.dumps(auth_token.user).replace("'", "\\'")
            html_response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Autenticación Exitosa</title>
                <script>
                    console.log('[OAuth] Storing token in localStorage');
                    // Almacenar token en localStorage
                    localStorage.setItem('access_token', '{auth_token.access_token}');
                    localStorage.setItem('user_data', '{user_data_json}');
                    
                    console.log('[OAuth] Token stored, redirecting to:', '{frontend_domain}{redirect_to}');
                    // Redirigir al dashboard del frontend
                    window.location.href = '{frontend_domain}{redirect_to}';
                </script>
            </head>
            <body>
                <p>Autenticación exitosa, redirigiendo...</p>
            </body>
            </html>
            """
            
            return HTMLResponse(html_response)
            
        except Exception as auth_error:
            logger.error(f"[OAuth] Error de autenticación: {auth_error}")
            return HTMLResponse(f"""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>No se pudo completar la autenticación: {str(auth_error)}</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)
            
    except Exception as e:
        logger.error(f"[OAuth] Error en callback: {e}")
        return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>Error</h2>
                <p>Ha ocurrido un error inesperado.</p>
                <a href="/login">Volver al Login</a>
            </body>
            </html>
        """, status_code=500)

@oauth_redirect_router.get("/google/callback")
async def oauth_google_callback_handler(request: Request, state: str = None, code: str = None):
    """
    Endpoint específico para Google OAuth callback - /auth/google/callback
    Este endpoint maneja redirecciones desde Google cuando está configurado así
    """
    try:
        logger.info(f"[OAuth] Google callback capturado en /auth/google/callback")
        logger.info(f"[OAuth] State: {state}, Code: {code[:20]}..." if code else "No code")
        
        # Procesar el callback directamente aquí
        if not state or not code:
            logger.error("[OAuth] Faltan parámetros state o code")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>Faltan parámetros requeridos para la autenticación.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)

        # Parsear y validar state
        state_data = _parse_state(state)
        if not state_data:
            logger.error("[OAuth] State inválido o expirado")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>La sesión de autenticación ha expirado.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)
        
        redirect_to = state_data.get("n", "/dashboard")
        
        # Autenticar con Google usando el redirect URI correcto
        try:
            # Use the correct redirect URI for Google callback
            public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip('/')
            if public_base:
                correct_redirect_uri = f"{public_base}/auth/google/callback"
            else:
                host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
                proto = request.headers.get("x-forwarded-proto") or request.url.scheme or 'https'
                correct_redirect_uri = f"{proto}://{host}/auth/google/callback"
                
            logger.info(f"[OAuth] Intentando autenticación con redirect_uri: {correct_redirect_uri}")
            auth_token = await google_auth.authenticate_with_google(code, redirect_override=correct_redirect_uri)
            
            # Generar HTML de respuesta que almacena el token y redirige al frontend
            frontend_domain = "https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io"
            user_data_json = json.dumps(auth_token.user).replace("'", "\\'")
            html_response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Autenticación Exitosa</title>
                <script>
                    console.log('[OAuth] Storing token in localStorage');
                    // Almacenar token en localStorage
                    localStorage.setItem('access_token', '{auth_token.access_token}');
                    localStorage.setItem('user_data', '{user_data_json}');
                    
                    console.log('[OAuth] Token stored, redirecting to:', '{frontend_domain}{redirect_to}');
                    // Redirigir al dashboard del frontend
                    window.location.href = '{frontend_domain}{redirect_to}';
                </script>
            </head>
            <body>
                <p>Autenticación exitosa, redirigiendo...</p>
            </body>
            </html>
            """
            
            return HTMLResponse(html_response)
            
        except Exception as auth_error:
            logger.error(f"[OAuth] Error de autenticación: {auth_error}")
            return HTMLResponse(f"""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>No se pudo completar la autenticación: {str(auth_error)}</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)
            
    except Exception as e:
        logger.error(f"[OAuth] Error en google callback: {e}")
        return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>Error</h2>
                <p>Ha ocurrido un error inesperado.</p>
                <a href="/login">Volver al Login</a>
            </body>
            </html>
        """, status_code=500)

@oauth_redirect_router.get("/google/callback/redirect")
async def oauth_redirect_handler(request: Request, state: str = None, code: str = None):
    """
    Endpoint para manejar redirecciones de OAuth que lleguen sin el prefijo /api
    Procesa directamente el callback en lugar de crear un loop de redirecciones
    """
    try:
        logger.info(f"[OAuth] Callback directo capturado en /auth/google/callback/redirect")
        logger.info(f"[OAuth] State: {state}, Code: {code[:20]}..." if code else "No code")
        
        # Procesar el callback directamente aquí usando la misma lógica del endpoint /api
        if not state or not code:
            logger.error("[OAuth] Faltan parámetros state o code")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>Faltan parámetros requeridos para la autenticación.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)

        # Parsear y validar state
        state_data = _parse_state(state)
        if not state_data:
            logger.error("[OAuth] State inválido o expirado")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>La sesión de autenticación ha expirado.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=400)
        
        redirect_to = state_data.get("n", "/dashboard")
        
        # Autenticar con Google usando el código
        # Use the correct redirect URI that matches what Google expects
        correct_redirect_uri = None
        try:
            # First try with the URI Google actually redirected to
            public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip('/')
            if public_base:
                correct_redirect_uri = f"{public_base}/auth/google/callback/redirect"
            else:
                host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
                proto = request.headers.get("x-forwarded-proto") or request.url.scheme or 'https'
                correct_redirect_uri = f"{proto}://{host}/auth/google/callback/redirect"
                
            logger.info(f"[OAuth] Intentando autenticación con redirect_uri: {correct_redirect_uri}")
            auth_token = await google_auth.authenticate_with_google(code, redirect_override=correct_redirect_uri)
            
        except HTTPException as he:
            logger.warning(f"[OAuth] Error con redirect_uri {correct_redirect_uri}: {he.detail}")
            if 'redirect_uri' in str(getattr(he, 'detail', '')).lower():
                logger.warning('[OAuth] Retry sin override por mismatch redirect_uri')
                try:
                    auth_token = await google_auth.authenticate_with_google(code, redirect_override=None)
                except Exception as e2:
                    logger.error(f"[OAuth] Falló también sin override: {e2}")
                    return HTMLResponse("""
                        <!DOCTYPE html>
                        <html>
                        <head><title>Error de Autenticación</title></head>
                        <body>
                            <h2>Error de Autenticación</h2>
                            <p>No se pudo completar la autenticación con Google. Verifique la configuración OAuth.</p>
                            <a href="/login">Volver al Login</a>
                        </body>
                        </html>
                    """, status_code=400)
            else:
                logger.error(f"[OAuth] Error de autenticación: {he.detail}")
                return HTMLResponse("""
                    <!DOCTYPE html>
                    <html>
                    <head><title>Error de Autenticación</title></head>
                    <body>
                        <h2>Error de Autenticación</h2>
                        <p>Error durante la autenticación con Google.</p>
                        <a href="/login">Volver al Login</a>
                    </body>
                    </html>
                """, status_code=400)
        except Exception as e:
            logger.error(f"[OAuth] Error inesperado durante autenticación: {e}")
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Error de Autenticación</title></head>
                <body>
                    <h2>Error de Autenticación</h2>
                    <p>Error interno del servidor. Por favor intente de nuevo.</p>
                    <a href="/login">Volver al Login</a>
                </body>
                </html>
            """, status_code=500)
        
        logger.info(f"[OAuth] Usuario autenticado exitosamente")
        
        # Obtener la URL del frontend desde variables de entorno o derivarla del host
        public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip('/')
        frontend_url = os.getenv("FRONTEND_URL")
        
        if not frontend_url:
            # Si no hay FRONTEND_URL configurada, usar el mismo dominio pero apuntar al frontend
            if public_base:
                frontend_url = public_base
            else:
                # Derivar del request actual
                host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
                proto = request.headers.get("x-forwarded-proto") or request.url.scheme or 'https'
                frontend_url = f"{proto}://{host}"
        
        # Construir URL completa de redirección
        full_redirect_url = f"{frontend_url}{redirect_to}"
        
        logger.info(f"[OAuth] Redirigiendo a: {full_redirect_url}")
        
        # Retornar HTML con script para guardar token y redirigir
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Autenticación Exitosa</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
        .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 20px auto; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div>
        <h2>Autenticación exitosa</h2>
        <div class="spinner"></div>
        <p>Guardando credenciales y redirigiendo...</p>
    </div>
    <script>
        console.log('[Auth] Iniciando proceso de autenticación');
        
        try {{
            var token = {auth_token.access_token!r};
            var redirectUrl = {full_redirect_url!r};
            
            console.log('[Auth] Token recibido:', token.substring(0, 20) + '...');
            console.log('[Auth] Redirigiendo a:', redirectUrl);
            
            // Guardar token en todas las formas posibles
            localStorage.setItem('access_token', token);
            sessionStorage.setItem('access_token', token);
            
            // Cookie con configuración más permisiva
            var cookieStr = 'access_token=' + token + '; Path=/; SameSite=Lax; Max-Age=86400';
            if (location.protocol === 'https:') {{
                cookieStr += '; Secure';
            }}
            document.cookie = cookieStr;
            
            console.log('[Auth] Token guardado en localStorage, sessionStorage y cookie');
            
            // Verificar que se guardó
            var stored = localStorage.getItem('access_token');
            if (stored === token) {{
                console.log('[Auth] Token verificado exitosamente');
                
                // Redirigir inmediatamente
                console.log('[Auth] Iniciando redirección...');
                window.location.href = redirectUrl;
                
            }} else {{
                console.error('[Auth] Error: token no se guardó correctamente');
                throw new Error('Token no se guardó en localStorage');
            }}
            
        }} catch(e) {{
            console.error('[Auth] Error procesando autenticación:', e);
            document.body.innerHTML = '<h2>Error de Autenticación</h2><p>Error: ' + e.message + '</p><p><a href="{frontend_url}/login">Intentar de nuevo</a></p>';
        }}
    </script>
</body>
</html>"""

        # Set cookie on response
        secure_flag = (request.headers.get('x-forwarded-proto') == 'https') or (request.url.scheme == 'https')
        from datetime import timedelta
        resp = HTMLResponse(content=html_content)
        resp.set_cookie(
            key="access_token",
            value=auth_token.access_token,
            max_age=int(timedelta(hours=24).total_seconds()),
            httponly=False,
            secure=secure_flag,
            samesite="Lax",
            path="/"
        )
        return resp
        
    except Exception as e:
        logger.error(f"[OAuth] Error en redirección: {e}")
        return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error de Autenticación</title>
            </head>
            <body>
                <h1>Error de Autenticación</h1>
                <p>Hubo un problema procesando su solicitud de autenticación.</p>
                <p><a href="/login">Intentar de nuevo</a></p>
            </body>
            </html>
        """, status_code=500)