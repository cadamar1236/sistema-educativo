"""
Sistema de suscripciones con Stripe
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

# Configuración de Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Intentar importar stripe
try:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("⚠️ Stripe no está instalado. Instala con: pip install stripe")

class SubscriptionTier(str, Enum):
    """Niveles de suscripción"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionPlan(BaseModel):
    """Modelo de plan de suscripción"""
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    limits: Dict[str, Any]
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None

# Definición de planes
SUBSCRIPTION_PLANS = {
    SubscriptionTier.FREE: SubscriptionPlan(
        tier=SubscriptionTier.FREE,
        name="Plan Gratuito",
        price_monthly=0,
        price_yearly=0,
        features=[
            "Acceso básico a agentes educativos",
            "5 documentos por mes",
            "10 consultas por día",
            "Soporte por email"
        ],
        limits={
            "documents_per_month": 5,
            "queries_per_day": 10,
            "storage_mb": 100,
            "agents_access": ["tutor", "exam_generator"]
        }
    ),
    SubscriptionTier.BASIC: SubscriptionPlan(
        tier=SubscriptionTier.BASIC,
        name="Plan Básico",
        price_monthly=9.99,
        price_yearly=99.99,
        features=[
            "Acceso a todos los agentes educativos",
            "50 documentos por mes",
            "100 consultas por día",
            "Análisis de rendimiento básico",
            "Soporte prioritario"
        ],
        limits={
            "documents_per_month": 50,
            "queries_per_day": 100,
            "storage_mb": 1000,
            "agents_access": "all"
        },
        stripe_price_id_monthly="price_basic_monthly",  # Reemplazar con IDs reales de Stripe
        stripe_price_id_yearly="price_basic_yearly"
    ),
    SubscriptionTier.PRO: SubscriptionPlan(
        tier=SubscriptionTier.PRO,
        name="Plan Profesional",
        price_monthly=29.99,
        price_yearly=299.99,
        features=[
            "Todo lo del plan Básico",
            "Documentos ilimitados",
            "500 consultas por día",
            "Análisis avanzado con IA",
            "Personalización de agentes",
            "API access",
            "Soporte 24/7"
        ],
        limits={
            "documents_per_month": -1,  # Ilimitado
            "queries_per_day": 500,
            "storage_mb": 10000,
            "agents_access": "all",
            "api_access": True,
            "custom_agents": True
        },
        stripe_price_id_monthly="price_pro_monthly",
        stripe_price_id_yearly="price_pro_yearly"
    ),
    SubscriptionTier.ENTERPRISE: SubscriptionPlan(
        tier=SubscriptionTier.ENTERPRISE,
        name="Plan Empresarial",
        price_monthly=99.99,
        price_yearly=999.99,
        features=[
            "Todo lo del plan Profesional",
            "Uso ilimitado",
            "Múltiples usuarios",
            "Agentes personalizados",
            "Integración con LMS",
            "SLA garantizado",
            "Soporte dedicado"
        ],
        limits={
            "documents_per_month": -1,
            "queries_per_day": -1,
            "storage_mb": -1,
            "agents_access": "all",
            "api_access": True,
            "custom_agents": True,
            "multi_user": True,
            "lms_integration": True
        },
        stripe_price_id_monthly="price_enterprise_monthly",
        stripe_price_id_yearly="price_enterprise_yearly"
    )
}

class StripeSubscriptionService:
    """Servicio de gestión de suscripciones con Stripe"""
    
    def __init__(self):
        self.stripe_available = STRIPE_AVAILABLE
        self.plans = SUBSCRIPTION_PLANS
        
        if not self.stripe_available:
            logger.warning("⚠️ Stripe no disponible - usando modo simulado")
    
    async def create_customer(self, email: str, name: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crear un cliente en Stripe"""
        if not self.stripe_available:
            return {
                "id": f"sim_cus_{email.replace('@', '_')}",
                "email": email,
                "name": name,
                "metadata": metadata or {}
            }
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "metadata": customer.metadata
            }
        except Exception as e:
            logger.error(f"Error creando cliente en Stripe: {e}")
            raise
    
    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Crear sesión de checkout en Stripe"""
        if not self.stripe_available:
            return {
                "id": "sim_checkout_session",
                "url": f"{success_url}?session_id=simulated",
                "success_url": success_url,
                "cancel_url": cancel_url
            }
        
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            
            return {
                "id": session.id,
                "url": session.url,
                "success_url": success_url,
                "cancel_url": cancel_url
            }
        except Exception as e:
            logger.error(f"Error creando sesión de checkout: {e}")
            raise
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Obtener información de una suscripción"""
        if not self.stripe_available:
            return {
                "id": subscription_id,
                "status": "active",
                "current_period_end": datetime.now().timestamp() + 30 * 24 * 3600,
                "tier": SubscriptionTier.FREE
            }
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Determinar el tier basado en el price_id
            tier = SubscriptionTier.FREE
            for plan_tier, plan in self.plans.items():
                if subscription.items.data[0].price.id in [plan.stripe_price_id_monthly, plan.stripe_price_id_yearly]:
                    tier = plan_tier
                    break
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "tier": tier,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        except Exception as e:
            logger.error(f"Error obteniendo suscripción: {e}")
            return None
    
    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancelar una suscripción"""
        if not self.stripe_available:
            return True
        
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.delete(subscription_id)
            
            return True
        except Exception as e:
            logger.error(f"Error cancelando suscripción: {e}")
            return False
    
    async def update_subscription(self, subscription_id: str, new_price_id: str) -> Dict[str, Any]:
        """Actualizar una suscripción a un nuevo plan"""
        if not self.stripe_available:
            return {
                "id": subscription_id,
                "status": "active",
                "updated": True
            }
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Actualizar el item de la suscripción
            stripe.SubscriptionItem.modify(
                subscription.items.data[0].id,
                price=new_price_id
            )
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "updated": True
            }
        except Exception as e:
            logger.error(f"Error actualizando suscripción: {e}")
            raise
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Manejar webhooks de Stripe"""
        if not self.stripe_available:
            return {"status": "simulated"}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            
            # Manejar diferentes tipos de eventos
            if event.type == 'checkout.session.completed':
                session = event.data.object
                # Aquí actualizarías la BD con la nueva suscripción
                logger.info(f"Checkout completado: {session.id}")
                
            elif event.type == 'customer.subscription.updated':
                subscription = event.data.object
                # Actualizar estado de suscripción en BD
                logger.info(f"Suscripción actualizada: {subscription.id}")
                
            elif event.type == 'customer.subscription.deleted':
                subscription = event.data.object
                # Marcar suscripción como cancelada en BD
                logger.info(f"Suscripción cancelada: {subscription.id}")
            
            return {"status": "success", "event_type": event.type}
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            raise
    
    def check_usage_limits(self, user_tier: SubscriptionTier, usage_type: str, current_usage: int) -> bool:
        """Verificar si el usuario ha alcanzado los límites de su plan"""
        plan = self.plans.get(user_tier)
        if not plan:
            return False
        
        limit = plan.limits.get(usage_type, 0)
        if limit == -1:  # Ilimitado
            return True
        
        return current_usage < limit
    
    def get_plan_features(self, tier: SubscriptionTier) -> SubscriptionPlan:
        """Obtener las características de un plan"""
        return self.plans.get(tier, self.plans[SubscriptionTier.FREE])

# Instancia global
stripe_service = StripeSubscriptionService()