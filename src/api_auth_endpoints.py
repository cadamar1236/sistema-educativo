"""
Endpoints de autenticación con Google y suscripciones con Stripe
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from typing import Dict, Any, Optional
import logging
import os

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

# ==================== ENDPOINTS DE AUTENTICACIÓN ====================

@auth_router.get("/google/login")
async def google_login(
    request: Request,
    redirect_url: Optional[str] = None,
    backend_redirect: bool = False,
    next: str = "/dashboard",
    force_http_loopback: bool = True,
    prefer_localhost: bool = True
):
    """Iniciar proceso de login con Google.
    Modos:
      - Frontend callback (default) -> página estática /auth/callback
      - backend_redirect=true -> backend intercambia y redirige
    Ajustes loopback: force_http_loopback, prefer_localhost ayudan a evitar redirect_uri mismatch.
    """
    try:
        raw_host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
        port = request.url.port
        proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        if prefer_localhost and raw_host and raw_host.startswith("127."):
            raw_host = "localhost"
        if force_http_loopback and (raw_host.startswith("localhost") or raw_host.startswith("127.")):
            proto = "http"
        if ':' not in raw_host and port and port not in (80, 443):
            host = f"{raw_host}:{port}"
        else:
            host = raw_host
        base_redirect = redirect_url
        if not base_redirect:
            if backend_redirect:
                base_redirect = f"{proto}://{host}/api/auth/google/callback/redirect"
            else:
                base_redirect = f"{proto}://{host}/auth/callback"
        base_redirect = base_redirect.split('?')[0].split('#')[0]
        if (not backend_redirect) and not base_redirect.rstrip('/').endswith('/auth/callback'):
            if base_redirect.endswith('/'):
                base_redirect = base_redirect.rstrip('/')
            base_redirect += '/auth/callback'
        
        # Usar la variable de entorno GOOGLE_REDIRECT_URI si está definida
        env_redirect = os.getenv("GOOGLE_REDIRECT_URI")
        if env_redirect:
            base_redirect = env_redirect
            
        auth_url = google_auth.get_authorization_url(redirect_override=base_redirect)
        logger.info(f"Google login mode={'backend' if backend_redirect else 'frontend'} redirect={base_redirect} host={host}")
        return {
            "auth_url": auth_url,
            "redirect_uri_used": base_redirect,
            "mode": "backend" if backend_redirect else "frontend",
            "next": next if backend_redirect else None,
            "message": "Redirige al usuario a esta URL para autenticación"
        }
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

@auth_router.get("/google/callback/redirect")
async def google_callback_redirect(
    request: Request,
    code: str = Query(...),
    state: Optional[str] = None,
    redirect_uri: Optional[str] = Query(None),
    next: str = Query("/dashboard")
):
    """Callback alternativo: el backend intercambia el código, guarda token (cookie + storage via JS) y redirige.
    Registra esta URL exacta en Google Console como redirect si usas modo backend_redirect."""
    try:
        effective_redirect = _normalize_redirect(_derive_effective_redirect(request, redirect_uri))
        try:
            auth_token = await google_auth.authenticate_with_google(code, redirect_override=effective_redirect)
        except HTTPException as he:
            detail = getattr(he, 'detail', '')
            if 'redirect_uri' in str(detail).lower():
                logger.warning("(redirect) retry sin override por redirect_uri mismatch")
                auth_token = await google_auth.authenticate_with_google(code, redirect_override=None)
            else:
                raise
        if not next.startswith('/'):
            next = '/'
        html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Autenticando...</title></head><body>
<script>
try {{
  const token = {auth_token.access_token!r};
  localStorage.setItem('access_token', token);
  sessionStorage.setItem('access_token', token);
  document.cookie = 'access_token=' + token + '; Path=/; SameSite=Lax';
  window.location.replace({next!r});
}} catch(e) {{
  document.body.innerHTML = 'Error almacenando token: ' + e;
}}
</script>
Redirigiendo...
</body></html>"""
        secure_flag = (request.url.scheme == 'https') or (request.headers.get('x-forwarded-proto') == 'https')
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
        raise HTTPException(status_code=400, detail="Error en autenticación con Google (redirect)")

@auth_router.get("/debug/config")
async def auth_debug_config(request: Request):
    """Diagnóstico de configuración OAuth para depurar fallos de callback."""
    host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    return {
        "host": host,
        "proto": proto,
        "env_GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI"),
        "default_service_redirect_uri": google_auth.redirect_uri,
        "suggested_frontend_callback": f"{proto}://{host}/auth/callback" if host else None,
        "suggested_backend_callback": f"{proto}://{host}/api/auth/google/callback/redirect" if host else None,
        "cookie_secure_example": (proto == 'https')
    }

@auth_router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return {
        "user": current_user,
        "subscription_tier": current_user.get("subscription_tier", "free"),
        "role": current_user.get("role", "student")
    }

@auth_router.post("/logout")
async def logout(response: Response):
    """Cerrar sesión"""
    # En una implementación real, invalidarías el token en la BD
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada exitosamente"}

@auth_router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Refrescar token de acceso"""
    try:
        # Obtener tier actualizado
        subscription_tier = await stripe_service.get_user_subscription_tier(current_user["sub"])

        # Crear nuevo token
        from auth.google_auth import GoogleUser
        user = GoogleUser(
            id=current_user["sub"],
            email=current_user["email"],
            name=current_user["name"],
            picture=current_user.get("picture", ""),
            verified_email=True
        )
        new_token = google_auth.create_jwt_token(
            user,
            subscription_tier,
            current_user.get("role", "student")
        )
        return {"access_token": new_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error refrescando token: {e}")
        raise HTTPException(status_code=500, detail="Error refrescando token")

@auth_router.post("/role/update")
async def set_user_role(payload: Dict[str, str], current_user: Dict[str, Any] = Depends(require_teacher)):
    """Actualizar rol de un usuario (simple: solo profesores pueden promover)."""
    email = payload.get("email")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=400, detail="email y role requeridos")
    if role not in {"student", "teacher"}:
        raise HTTPException(status_code=400, detail="rol inválido")
    ok = update_role(email, role)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"success": True, "email": email, "role": role}

# ==================== ENDPOINTS DE SUSCRIPCIÓN ====================

@subscription_router.get("/plans")
async def get_subscription_plans():
    """Obtener todos los planes de suscripción disponibles"""
    plans = []
    for tier, plan in stripe_service.plans.items():
        plans.append({
            "tier": tier.value,
            "name": plan.name,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "features": plan.features,
            "limits": plan.limits
        })
    
    return {
        "plans": plans,
        "currency": "USD"
    }

@subscription_router.get("/current")
async def get_current_subscription(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Obtener suscripción actual del usuario"""
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