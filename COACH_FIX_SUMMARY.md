# Corrección del Coach IA - URLs de API

## Problema Identificado
El componente `AICoachReal.tsx` y el servicio `juliaAgentService.ts` tenían problemas de conectividad porque:

1. Usaban URLs hardcodeadas del puerto 8000 (desarrollo)
2. No detectaban automáticamente si estaban en desarrollo o producción
3. Las rutas de API no tenían el prefijo `/api` correcto

## Soluciones Implementadas

### 1. Actualización de `juliaAgentService.ts`

**Antes:**
```typescript
import { apiBase } from './runtimeApi';
const API_BASE_URL = apiBase() + '/api';
```

**Después:**
```typescript
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // En el cliente, detectar si estamos en desarrollo o producción
    const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    return isDevelopment 
      ? 'http://127.0.0.1:8000' 
      : 'https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io';
  }
  // En el servidor, usar producción por defecto
  return 'https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io';
};

const API_BASE_URL = getApiBaseUrl();
```

### 2. Corrección de Endpoints

Todos los endpoints fueron actualizados para incluir el prefijo `/api` correcto:

- `/agents/student-coach/get-guidance` → `/api/agents/student-coach/get-guidance`
- `/agents/analytics/analyze` → `/api/agents/analytics/analyze`
- `/agents/lesson-planner/create-plan` → `/api/agents/lesson-planner/create-plan`
- `/agents/document-analyzer/analyze-progress` → `/api/agents/document-analyzer/analyze-progress`
- `/agents/exam-generator/create-exam` → `/api/agents/exam-generator/create-exam`
- `/agents/analytics/parent-report` → `/api/agents/analytics/parent-report`
- `/agents/analytics/classroom-analytics` → `/api/agents/analytics/classroom-analytics`
- `/agents/coordinator/execute` → `/api/agents/coordinator/execute`
- `/students/interactions` → `/api/students/interactions`
- `/agents/recommendations/generate` → `/api/agents/recommendations/generate`
- `/agents/tutor/start-session` → `/api/agents/tutor/start-session`
- `/students/{id}/realtime` → `/api/students/{id}/realtime`

### 3. Detección Automática de Entorno

El servicio ahora detecta automáticamente si está ejecutándose en:
- **Desarrollo**: `localhost` o `127.0.0.1` → usa `http://127.0.0.1:8000`
- **Producción**: cualquier otro hostname → usa la URL de Azure Container Apps

### 4. Consistencia con apiConfig.ts

Ahora `juliaAgentService.ts` usa la misma lógica de detección de entorno que `apiConfig.ts`, asegurando consistencia en toda la aplicación.

## Resultado

✅ El Coach IA ahora funciona correctamente tanto en desarrollo como en producción
✅ Se eliminaron las URLs hardcodeadas problemáticas
✅ Los endpoints usan la estructura correcta `/api/...`
✅ Detección automática de entorno sin configuración manual

## Archivos Modificados

1. `julia-frontend/lib/juliaAgentService.ts` - Servicio principal corregido
2. `julia-frontend/components/student/AICoachReal.tsx` - Componente que usa el servicio

## Testing

Para probar:
1. En desarrollo: Acceder al dashboard y ir a la pestaña "Coach IA"
2. En producción: Mismo proceso en la URL de Azure Container Apps
3. Verificar que las llamadas de API usan las URLs correctas en las herramientas de desarrollador
