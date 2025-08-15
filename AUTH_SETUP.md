# 🔐 Configuración de Autenticación con Google y Suscripciones con Stripe

## 📋 Resumen de Cambios

### 1. **Solución al Error de Azure Search**
- ✅ Implementado fallback automático a almacenamiento local
- ✅ Si Azure Search no está disponible, usa base de datos local
- ✅ No requiere Azure Search para funcionar

### 2. **Autenticación con Google OAuth**
- ✅ Login con cuenta de Google
- ✅ Tokens JWT seguros
- ✅ Sesiones persistentes
- ✅ Refresh tokens automático

### 3. **Sistema de Suscripciones con Stripe**
- ✅ 4 planes: Free, Basic, Pro, Enterprise
- ✅ Pagos mensuales y anuales
- ✅ Checkout seguro con Stripe
- ✅ Gestión de límites por plan

## 🚀 Instalación Rápida

### Paso 1: Instalar Dependencias
```bash
# En Windows
pip install httpx PyJWT stripe azure-search-documents

# O usar el script de instalación
./install_auth_deps.sh
```

### Paso 2: Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env y agregar tus claves
```

### Paso 3: Configurar Google OAuth

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Ve a "APIs & Services" > "Credentials"
4. Crea un "OAuth 2.0 Client ID"
5. Configura:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:3000/auth/callback`
6. Copia el Client ID y Client Secret a tu `.env`

### Paso 4: Configurar Stripe

1. Ve a [Stripe Dashboard](https://dashboard.stripe.com/)
2. Obtén tus claves API (test mode para desarrollo)
3. Crea productos y precios para cada plan:
   - Plan Basic: $9.99/mes, $99.99/año
   - Plan Pro: $29.99/mes, $299.99/año
   - Plan Enterprise: $99.99/mes, $999.99/año
4. Copia las claves a tu `.env`

## 📁 Archivos Creados

### Backend
- `src/azure_search_config.py` - Configuración de Azure con fallback local
- `agents/educational_rag/agent_fixed.py` - Agente RAG mejorado con fallback
- `src/auth/google_auth.py` - Sistema de autenticación con Google
- `src/payments/stripe_subscription.py` - Sistema de suscripciones
- `src/api_auth_endpoints.py` - Endpoints de API para auth y suscripciones

### Frontend
- `julia-frontend/components/auth/GoogleLoginButton.tsx` - Botón de login
- `julia-frontend/components/subscription/SubscriptionPlans.tsx` - Planes de suscripción
- `julia-frontend/hooks/useAuth.ts` - Hook de autenticación
- `julia-frontend/pages/auth/callback.tsx` - Página de callback OAuth

## 🔧 Configuración del .env

```env
# Google OAuth
GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Stripe
STRIPE_SECRET_KEY=sk_test_tu_clave_secreta
STRIPE_PUBLISHABLE_KEY=pk_test_tu_clave_publica
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret

# JWT
JWT_SECRET=una_clave_super_secreta_cambiala_en_produccion

# Azure Search (Opcional - si no está, usa local)
AZURE_SEARCH_SERVICE_NAME=juliaai
AZURE_SEARCH_ADMIN_KEY=tu_clave_si_tienes
USE_LOCAL_FALLBACK=true
```

## 🎯 Uso en el Frontend

### Login con Google
```tsx
import { GoogleLoginButton } from '@/components/auth/GoogleLoginButton';

<GoogleLoginButton onLogin={() => console.log('Login exitoso')} />
```

### Mostrar Planes de Suscripción
```tsx
import { SubscriptionPlans } from '@/components/subscription/SubscriptionPlans';

<SubscriptionPlans />
```

### Usar el Hook de Autenticación
```tsx
import { useAuth } from '@/hooks/useAuth';

function MyComponent() {
  const { user, isAuthenticated, logout, subscriptionTier } = useAuth();
  
  if (!isAuthenticated) {
    return <div>Por favor inicia sesión</div>;
  }
  
  return (
    <div>
      <p>Hola, {user.name}!</p>
      <p>Plan: {subscriptionTier}</p>
      <button onClick={logout}>Cerrar Sesión</button>
    </div>
  );
}
```

## 🔒 Proteger Endpoints con Suscripción

### En el Backend
```python
from auth.google_auth import require_subscription

@app.get("/api/premium-feature")
async def premium_feature(user = Depends(require_subscription("pro"))):
    # Solo usuarios Pro o Enterprise pueden acceder
    return {"data": "contenido premium"}
```

### En el Frontend
```tsx
const { requireAuth } = useAuth();

const accessPremiumFeature = () => {
  if (requireAuth('pro')) {
    // Usuario tiene plan Pro o superior
    // Mostrar contenido premium
  }
};
```

## 🐛 Solución de Problemas

### Error: "Failed to resolve 'juliaai.search.windows.net'"
**Solución**: El sistema automáticamente usará almacenamiento local. No se requiere acción.

### Error: "Google OAuth no configurado"
**Solución**: Asegúrate de tener las variables GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en tu .env

### Error: "Stripe no disponible"
**Solución**: Instala stripe con `pip install stripe`

## 📊 Límites por Plan

| Característica | Free | Basic | Pro | Enterprise |
|---------------|------|-------|-----|------------|
| Documentos/mes | 5 | 50 | Ilimitado | Ilimitado |
| Consultas/día | 10 | 100 | 500 | Ilimitado |
| Almacenamiento | 100MB | 1GB | 10GB | Ilimitado |
| Agentes IA | 2 | Todos | Todos | Todos |
| API Access | ❌ | ❌ | ✅ | ✅ |
| Soporte | Email | Prioritario | 24/7 | Dedicado |

## 🚀 Próximos Pasos

1. **Configurar base de datos**: Para persistir usuarios y suscripciones
2. **Configurar webhooks de Stripe**: Para actualizaciones automáticas
3. **Implementar dashboard de administración**: Para gestionar usuarios
4. **Agregar más proveedores OAuth**: Facebook, Microsoft, etc.

## 📞 Soporte

Si tienes problemas con la configuración, verifica:
1. Todas las dependencias están instaladas
2. Las variables de entorno están configuradas
3. Los servicios externos (Google, Stripe) están configurados correctamente

---

✨ **Sistema completamente funcional con fallback local para Azure Search!**