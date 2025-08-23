"""
Endpoints de autenticación con Google y suscripciones con Stripe
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
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
async def google_login(request: Request, redirect_url: Optional[str] = None):
    """Iniciar proceso de login con Google.
    Determina automáticamente el redirect_uri productivo basado en host si no se proporciona uno válido."""
    try:
        base_redirect = redirect_url
        # Si no se pasa redirect_url y estamos fuera de localhost, construir usando host
        host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
        proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        if not base_redirect:
            if host and not host.startswith("localhost") and not host.startswith("127."):
                base_redirect = f"{proto}://{host}/auth/callback"
        # Normalizar: garantizar path /auth/callback
        if base_redirect and not base_redirect.endswith("/auth/callback"):
            if base_redirect.endswith('/'):
                base_redirect = base_redirect.rstrip('/') + '/auth/callback'
            else:
                base_redirect = base_redirect + '/auth/callback'

        # Obtener URL de autorización con override si corresponde
        auth_url = google_auth.get_authorization_url(redirect_override=base_redirect)
        return {
            "auth_url": auth_url,
            "redirect_uri_used": base_redirect or google_auth.redirect_uri,
            "message": "Redirige al usuario a esta URL para autenticación"
        }
    except Exception as e:
        logger.error(f"Error iniciando login con Google: {e}")
        raise HTTPException(status_code=500, detail="Error iniciando autenticación")

@auth_router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: Optional[str] = None,
    redirect_uri: Optional[str] = Query(None)
):
    """Callback de Google OAuth.
    Si no se proporciona redirect_uri explícito, intenta derivarlo dinámicamente del host para evitar
    el error típico de "redirect_uri_mismatch" cuando en el login se usó un dominio productivo y
    aquí se intenta intercambiar con el valor por defecto (localhost)."""
    try:
        derived_redirect = None
        if not redirect_uri:
            host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
            proto = request.headers.get("x-forwarded-proto") or request.url.scheme
            if host:
                # Priorizar variable de entorno si existe (ya debería tener la ruta correcta)
                env_redirect = os.getenv("GOOGLE_REDIRECT_URI", "")
                if env_redirect and host in env_redirect:
                    derived_redirect = env_redirect
                else:
                    # Soportar ambos posibles paths registrados: /auth/callback y /auth/google/callback
                    # Escoger según lo que esté registrado en env si existe, si no /auth/callback por defecto.
                    if env_redirect:
                        # Reemplazar sólo el origen manteniendo path del env
                        try:
                            from urllib.parse import urlparse
                            p = urlparse(env_redirect)
                            derived_redirect = f"{proto}://{host}{p.path}"
                        except Exception:
                            derived_redirect = f"{proto}://{host}/auth/callback"
                    else:
                        derived_redirect = f"{proto}://{host}/auth/callback"
        effective_redirect = redirect_uri or derived_redirect

        auth_token = await google_auth.authenticate_with_google(code, redirect_override=effective_redirect)

        return {
            "success": True,
            "access_token": auth_token.access_token,
            "user": auth_token.user,
            "message": "Autenticación exitosa",
            "redirect_uri_used": effective_redirect or google_auth.redirect_uri
        }
    except Exception as e:
        logger.error(f"Error en callback de Google: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Error en autenticación con Google (callback)")

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