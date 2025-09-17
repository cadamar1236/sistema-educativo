"""
API principal del sistema educativo multiagente - versión simplificada
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import uvicorn
from typing import List, Optional, Dict, Any
import json
import sys
import os
import time
import re
from datetime import datetime, timedelta
import uuid
import os, random
try:
    import redis  # type: ignore
except ImportError:
    redis = None

# Agregar el directorio padre al path para imports absolutos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importaciones básicas
from src.config import settings
from src.models import AgentType

# Función auxiliar para extraer información de usuario desde el token
def extract_user_from_request(request) -> Optional[Dict[str, Any]]:
    """Extrae información del usuario desde el token JWT en el header Authorization"""
    try:
        # Buscar el token en el header Authorization
        auth_header = request.headers.get("authorization")
        if not auth_header:
            print("🔍 Debug auth: No authorization header found")
            return None
            
        if not auth_header.startswith("Bearer "):
            print(f"🔍 Debug auth: Invalid auth header format: {auth_header[:50]}...")
            return None
            
        token = auth_header.split(" ")[1]
        print(f"🔍 Debug auth: Token found, length: {len(token)}")
        
        # Importar el servicio de autenticación
        try:
            from src.auth.google_auth import GoogleAuthService
        except ImportError:
            try:
                from auth.google_auth import GoogleAuthService
            except ImportError:
                print("🔍 Debug auth: Could not import GoogleAuthService")
                return None
        
        auth_service = GoogleAuthService()
        payload = auth_service.verify_jwt_token(token)
        print(f"🔍 Debug auth: Token verified, payload: {payload}")
        return payload
        
    except Exception as e:
        print(f"🔍 Debug auth: Exception in extract_user_from_request: {e}")
        return None

def normalize_student_id(identifier: str) -> str:
    """Normaliza un email o ID a un formato válido para el servicio de estadísticas"""
    if "@" in identifier:
        return identifier.replace("@", "_at_").replace(".", "_dot_")
    return identifier

# Servicios - Priorizar base de datos PostgreSQL
try:
    from src.services.database_student_stats_service import DatabaseStudentStatsService
    student_stats_service = DatabaseStudentStatsService()
    print("✅ Usando servicio de estadísticas con PostgreSQL")
except ImportError as e:
    try:
        from src.services.student_stats_service import student_stats_service
        print("⚠️ Usando servicio de estadísticas con archivos JSON (fallback)")
    except ImportError:
        print("❌ No se pudo cargar ningún servicio de estadísticas")
        student_stats_service = None

from src.services.assignment_service import assignment_service

# Importar agentes reales
AGENTS_INIT_ERROR = None
try:
    from agents import (
        ExamGeneratorAgent,
        CurriculumCreatorAgent,
        TutorAgent,
        LessonPlannerAgent,
        DocumentAnalyzerAgent
    )
    from agents.student_coach.agent import StudentCoachAgent
    from agents.educational_rag.agent import EducationalRAGAgent
    from fixed_base_agent import EnhancedEducationalAgent
    from src.services.coaching_database_service import get_coaching_db_service
    # Validar API Key antes de marcar disponibles
    if not getattr(settings, 'groq_api_key', None):
        raise ValueError("GROQ_API_KEY no encontrada en configuración (.env)")
    AGENTS_AVAILABLE = True
    print("✅ Agentes reales importados correctamente (incluyendo Educational RAG)")
except Exception as e:
    AGENTS_AVAILABLE = False
    AGENTS_INIT_ERROR = str(e)
    print(f"⚠️ Error importando agentes reales: {e}")
    print("🔄 Usando modo simulado - establece GROQ_API_KEY y reinstala dependencias si falta 'groq'")

# Biblioteca deshabilitada por complejidad
REAL_LIBRARY_AVAILABLE = False
print("⚠️ Biblioteca deshabilitada - funcionalidad removida por complejidad")

# Asegurar que el propio directorio src esté en el path para imports relativos directos
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

"""Import robusto de routers de autenticación.
Si falla, mostramos diagnóstico detallado para evitar 404 silencioso en /api/auth/google/login."""
_AUTH_ROUTERS_AVAILABLE = False
_auth_import_errors = {}
import importlib, types

def _attempt_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception as e:  # registrar error
        _auth_import_errors[name] = repr(e)
        return None

mod_candidates = [
    'src.api_auth_endpoints',  # paquete completo
    'api_auth_endpoints',      # nivel superior
    __name__.rsplit('.',1)[0] + '.api_auth_endpoints' if '.' in __name__ else None,
]
seen = set()
oauth_redirect_router = None  # Inicializar variable
for cand in [c for c in mod_candidates if c and c not in seen]:
    seen.add(cand)
    mod = _attempt_import(cand)
    if isinstance(mod, types.ModuleType) and hasattr(mod, 'auth_router') and hasattr(mod, 'subscription_router'):
        auth_router = getattr(mod, 'auth_router')  # type: ignore
        subscription_router = getattr(mod, 'subscription_router')  # type: ignore
        # Intentar importar también oauth_redirect_router si existe
        oauth_redirect_router = getattr(mod, 'oauth_redirect_router', None) if hasattr(mod, 'oauth_redirect_router') else None
        _AUTH_ROUTERS_AVAILABLE = True
        print(f"✅ auth_router importado desde '{cand}'")
        if oauth_redirect_router:
            print(f"✅ oauth_redirect_router también importado")
        break

if not _AUTH_ROUTERS_AVAILABLE:
    print("❌ No se pudo importar auth_router. Intentos:", _auth_import_errors)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema Educativo Multiagente",
    description="Sistema integral de agentes inteligentes para instituciones educativas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""Eliminado middleware de debug de chunks para simplificar el servidor."""

# Endpoint de health simple para healthchecks de Docker / Azure
@app.get("/health")
async def health():
    return {"status": "ok"}

# Debug: listar rutas y config OAuth (no exponer secretos)
@app.get("/debug/routes")
def debug_routes():
    return {
        "count": len(app.routes),
        "paths": [r.path for r in app.routes if hasattr(r, 'path')]
    }

@app.get("/debug/authinfo")
def debug_authinfo():
    info = {}
    try:
        try:
            from src.auth.google_auth import google_auth as _ga  # type: ignore
        except Exception:
            from auth.google_auth import google_auth as _ga  # type: ignore
        info["google_redirect_uri_instance"] = getattr(_ga, 'redirect_uri', None)
    except Exception as e:
        info["google_auth_import_error"] = repr(e)
    # Env (enmascarar client secret)
    info["env_GOOGLE_REDIRECT_URI"] = os.getenv("GOOGLE_REDIRECT_URI")
    cid = os.getenv("GOOGLE_CLIENT_ID", "")
    info["env_GOOGLE_CLIENT_ID_suffix"] = cid[-12:] if len(cid) > 12 else cid
    info["has_GOOGLE_CLIENT_SECRET"] = bool(os.getenv("GOOGLE_CLIENT_SECRET"))
    # Confirmar ruta login registrada
    auth_paths = [r.path for r in app.routes if r.path.startswith('/api/auth/')]
    info["auth_paths"] = auth_paths
    info["login_route_present"] = '/api/auth/google/login' in auth_paths
    return info

# Registrar routers de auth si están disponibles (ANTES del catch-all)
if _AUTH_ROUTERS_AVAILABLE:
    try:
        app.include_router(auth_router)
        app.include_router(subscription_router)
        # Registrar también oauth_redirect_router si existe
        if oauth_redirect_router:
            app.include_router(oauth_redirect_router)
            print("✅ Routers de autenticación, suscripciones y OAuth redirect registrados (/api/auth, /api/subscription, /auth)")
        else:
            print("✅ Routers de autenticación y suscripciones registrados (/api/auth, /api/subscription)")
        auth_paths = [r.path for r in app.routes if r.path.startswith('/api/auth')]
        oauth_paths = [r.path for r in app.routes if r.path.startswith('/auth')]
        print("🔎 Rutas auth registradas:", auth_paths)
        print("🔎 Rutas OAuth redirect registradas:", oauth_paths)
        if '/api/auth/google/login' not in auth_paths:
            print("⚠️ Advertencia: /api/auth/google/login no aparece en el listado de rutas")
    except Exception as e:
        print("❌ Fallo al incluir routers de auth:", e)
        _AUTH_ROUTERS_AVAILABLE = False
else:
    print("ℹ️ Routers de autenticación no disponibles; endpoints OAuth no expuestos")

########## SERVING FRONTEND EXPORT (SIMPLIFICADO) ##########
FRONTEND_EXPORT_DIR = "static"  # Directorio donde copiamos el 'out' de Next.js
NEXT_ASSETS_DIR = os.path.join(FRONTEND_EXPORT_DIR, "_next")

def _is_route_mounted(prefix: str) -> bool:
    try:
        return any(getattr(r, 'path', '').startswith(prefix) for r in app.routes)
    except Exception:
        return False

def _mount_static_exports(initial=False):
    """Intenta montar /_next y /static si existen. safe idempotent."""
    if not os.path.isdir(FRONTEND_EXPORT_DIR):
        if initial:
            print("⚠️ No existe el directorio 'static' con el export del frontend. Ejecuta build/export de Next.js.")
        return
    # /static mount
    if not _is_route_mounted('/static'):
        try:
            app.mount("/static", StaticFiles(directory=FRONTEND_EXPORT_DIR), name="static")
            print("✅ (/static) directorio export montado")
        except Exception as e:
            print("❌ Error montando /static:", e)
    # /_next mount
    if os.path.isdir(NEXT_ASSETS_DIR) and not _is_route_mounted('/_next'):
        try:
            app.mount("/_next", StaticFiles(directory=NEXT_ASSETS_DIR), name="_next")
            print("✅ (/_next) bundles Next.js montados")
        except Exception as e:
            print("❌ Error montando /_next:", e)
    # Validación rápida de un chunk si existe el directorio de chunks
    chunks_dir = os.path.join(NEXT_ASSETS_DIR, 'static', 'chunks')
    if os.path.isdir(chunks_dir):
        try:
            sample = next((f for f in os.listdir(chunks_dir) if f.endswith('.js')), None)
            if sample:
                print(f"🔍 Chunk de ejemplo disponible: {sample}")
        except Exception as e:
            print("[STATIC DEBUG] Error listando chunks:", e)

_mount_static_exports(initial=True)

async def _delayed_next_mount(max_wait_seconds: int = 30):
    """Espera a que aparezca static/_next tras un build tardío y monta dinámicamente."""
    for i in range(max_wait_seconds):
        if _is_route_mounted('/_next'):
            return
        if os.path.isdir(NEXT_ASSETS_DIR):
            _mount_static_exports()
            return
        await asyncio.sleep(1)
    if not _is_route_mounted('/_next'):
        print(f"⌛ No se encontró static/_next tras {max_wait_seconds}s; los assets seguirán faltando hasta que hagas rebuild.")

@app.on_event("startup")
async def ensure_next_after_startup():
    # Si al inicio no estaba montado _next pero luego el usuario ejecuta el script de build, lo montamos.
    if not _is_route_mounted('/_next'):
        asyncio.create_task(_delayed_next_mount())

@app.get("/debug/remount-static")
def debug_remount_static():
    """Fuerza un reintento de montaje de static/_next (dev)."""
    before = {"_next": _is_route_mounted('/_next'), "static": _is_route_mounted('/static')}
    _mount_static_exports()
    after = {"_next": _is_route_mounted('/_next'), "static": _is_route_mounted('/static')}
    return {"before": before, "after": after, "exists": {"static": os.path.isdir(FRONTEND_EXPORT_DIR), "_next": os.path.isdir(NEXT_ASSETS_DIR)}}

@app.post("/api/agents/test-tracking")
async def test_tracking_endpoint():
    """Endpoint de prueba para verificar que el tracking automático funcione"""
    return JSONResponse(content={
        "success": True, 
        "message": "Tracking test endpoint called",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/debug/static-status")
def debug_static_status():
    """Estado detallado de los assets estáticos para diagnosticar errores 'Unexpected token <'."""
    chunks_dir = os.path.join(NEXT_ASSETS_DIR, 'static', 'chunks')
    chunk_list = []
    err = None
    if os.path.isdir(chunks_dir):
        try:
            chunk_list = sorted([f for f in os.listdir(chunks_dir) if f.endswith('.js')])[:25]
        except Exception as e:
            err = repr(e)
    return {
        "mounted": {"_next": _is_route_mounted('/_next'), "static": _is_route_mounted('/static')},
        "paths": {"frontend_root": os.path.abspath(FRONTEND_EXPORT_DIR), "next_dir": os.path.abspath(NEXT_ASSETS_DIR), "chunks_dir": chunks_dir},
        "exists": {"frontend_root": os.path.isdir(FRONTEND_EXPORT_DIR), "_next": os.path.isdir(NEXT_ASSETS_DIR), "chunks": os.path.isdir(chunks_dir)},
        "chunks_sample": chunk_list,
        "error_listing": err,
        "route_count": len(app.routes)
    }

########## FIN DEBUG AVANZADO (REMOVIDO) ##########

# Favicon específico
@app.get("/favicon.ico")
async def favicon():
    favicon_path = "static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/", response_class=HTMLResponse)
async def serve_root():
    index_path = os.path.join(FRONTEND_EXPORT_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend no exportado</h1><p>Ejecuta 'npm run build && npx next export' y copia 'out' a 'static'.</p>")

# API Endpoints - MUST be defined BEFORE catch-all route
@app.get("/api/students/{student_id}/dashboard-stats")
async def get_dashboard_stats_early(student_id: str = "student_001"):
    """
    Obtiene estadísticas completas del dashboard del estudiante
    
    Args:
        student_id: ID del estudiante o email
        
    Returns:
        Estadísticas completas del dashboard incluyendo progreso, actividades, logros, etc.
    """
    try:
        # URL decode el student_id en caso de que sea un email
        import urllib.parse
        decoded_student_id = urllib.parse.unquote(student_id)
        
        r = _get_redis()
        key = f"dashboard_stats:{decoded_student_id}"
        if r:
            cached = r.get(key)
            if cached:
                import json as _json
                data = _json.loads(cached)
                data["success"] = True
                data["student_id"] = decoded_student_id
                data["timestamp"] = datetime.now().isoformat()
                data["cache"] = True
                return JSONResponse(content=data)

        # Intentar obtener estadísticas reales del servicio
        try:
            # NO normalizar el email, usar directamente ya que ahora guardamos con el email real
            service_id = decoded_student_id
                
            dashboard_stats = student_stats_service.get_dashboard_stats(service_id)
            print(f"📈 Dashboard: Consultando stats para {service_id}")
            
            # Asegurarse de que el email original esté incluido en la respuesta
            if "student" in dashboard_stats and "@" in decoded_student_id:
                dashboard_stats["student"]["email"] = decoded_student_id
                dashboard_stats["student"]["id"] = decoded_student_id
                
            dashboard_stats["success"] = True
            dashboard_stats["student_id"] = decoded_student_id
            dashboard_stats["timestamp"] = datetime.now().isoformat()
            dashboard_stats["cache"] = False
            
            # Cache the result
            if r:
                import json as _json
                try:
                    r.set(key, _json.dumps(dashboard_stats), ex=random.randint(60,120))
                except Exception:
                    pass
            return JSONResponse(content=dashboard_stats)
            
        except Exception as service_error:
            print(f"Error en servicio de estadísticas: {service_error}")
            # Fallback to mock data if service fails
            
        # Crear estadísticas simuladas por ahora para evitar errores del servicio
        mock_dashboard_stats = {
            "student": {
                "name": "Usuario",
                "email": decoded_student_id if "@" in decoded_student_id else f"{decoded_student_id}@example.com",
                "id": decoded_student_id,
                "total_points": 850,
                "level": 5,
                "progress_percentage": 72
            },
            "total_assignments": 12,
            "completed_assignments": 8,
            "pending_assignments": 4,
            "average_score": 87.5,
            "recent_activities": [
                {"type": "assignment_completed", "title": "Matemáticas - Álgebra", "date": "2024-08-24", "score": 95},
                {"type": "quiz_taken", "title": "Historia Universal", "date": "2024-08-23", "score": 82},
                {"type": "assignment_submitted", "title": "Literatura Española", "date": "2024-08-22", "score": 88}
            ],
            "upcoming_deadlines": [
                {"type": "assignment", "title": "Proyecto de Ciencias", "due_date": "2024-08-30"},
                {"type": "exam", "title": "Examen de Matemáticas", "due_date": "2024-09-02"}
            ],
            "achievements": [
                {"title": "Estudiante Destacado", "date": "2024-08-20"},
                {"title": "Participación Activa", "date": "2024-08-15"}
            ],
            "study_streak": {"current": 7, "longest": 15},
            "course_progress": [
                {"course": "Matemáticas", "progress": 75, "grade": "A-"},
                {"course": "Historia", "progress": 60, "grade": "B+"},
                {"course": "Literatura", "progress": 85, "grade": "A"}
            ]
        }
        
        # Usar las estadísticas simuladas en lugar del servicio que puede fallar
        dashboard_stats = mock_dashboard_stats
        dashboard_stats["success"] = True
        dashboard_stats["student_id"] = decoded_student_id
        dashboard_stats["timestamp"] = datetime.now().isoformat()
        dashboard_stats["cache"] = False
        if r:
            import json as _json
            try:
                r.set(key, _json.dumps(dashboard_stats), ex=random.randint(60,120))
            except Exception:
                pass
        return JSONResponse(content=dashboard_stats)
    except Exception as e:
        print(f"Error obteniendo estadísticas del dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# Catch-all SPA (DESPUÉS de mounts y rutas API) — sirve index.html para rutas de aplicación
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_catch_all(full_path: str):
    # No interferir con rutas API ni assets
    if full_path.startswith(("api/", "_next/", "static/")) or full_path in ("favicon.ico", "robots.txt"):
        raise HTTPException(status_code=404)
    index_path = os.path.join(FRONTEND_EXPORT_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend no disponible")

# NO usar catch-all que interfiere con mounts estáticos

# === FUNCIONES AUXILIARES PARA TRACKING ===

def _get_subject_from_agent(agent_id: str) -> str:
    """Mapea agente a materia académica"""
    agent_subject_map = {
        "exam_generator": "Evaluación",
        "curriculum_creator": "Planificación",
        "tutor": "Tutoría General", 
        "lesson_planner": "Organización",
        "performance_analyzer": "Análisis Académico",
        "student_coach": "Coaching Estudiantil",
        "enhanced_agent": "Agente Mejorado",
        "educational_rag": "Biblioteca Educativa"
    }
    return agent_subject_map.get(agent_id, "General")

def _calculate_points_for_interaction(agent_id: str, message: str) -> int:
    """Calcula puntos basados en la interacción"""
    base_points = 10
    
    # Bonus por longitud del mensaje (engagement)
    if len(message) > 100:
        base_points += 5
    if len(message) > 200:
        base_points += 10
    
    # Bonus por tipo de agente
    agent_bonus = {
        "exam_generator": 15,  # Práctica de exámenes
        "tutor": 20,           # Sesiones de tutoría
        "lesson_planner": 10,  # Planificación
        "curriculum_creator": 12,
        "performance_analyzer": 8,
        "student_coach": 18,
        "enhanced_agent": 12,
        "educational_rag": 25  # RAG educativo premium
    }
    
    return base_points + agent_bonus.get(agent_id, 0)

# === MIDDLEWARE PARA TRACKING AUTOMÁTICO ===

@app.middleware("http")
async def track_requests(request, call_next):
    """Middleware para tracking automático de todas las interacciones"""
    import time
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)

    # DEBUG: Verificar archivos estáticos de Next.js que provocan "Unexpected token '<'"
    try:
        path = request.url.path  # e.g. /_next/static/chunks/webpack-xxx.js
        if path.startswith("/_next/"):
            # Traducir a ruta de archivo en disco
            relative = path[len("/_next/"):]  # static/chunks/...
            disk_path = os.path.join("static", "_next", relative.replace("/", os.sep))
            exists = os.path.exists(disk_path)
            size = os.path.getsize(disk_path) if exists else -1
            # Añadir cabeceras de depuración
            response.headers["X-Debug-Static-File"] = disk_path
            response.headers["X-Debug-Static-Exists"] = str(exists)
            response.headers["X-Debug-Static-Size"] = str(size)
            if not exists:
                print(f"[STATIC DEBUG] NO EXISTE archivo pedido: {disk_path}")
            else:
                if size < 40:
                    with open(disk_path, 'rb') as fdbg:
                        head = fdbg.read(60)
                    print(f"[STATIC DEBUG] Sirviendo {disk_path} bytes={size} inicio={head[:30]!r}")
    except Exception as _dbg_e:
        print(f"[STATIC DEBUG] Error debug estático: {_dbg_e}")
    
    # Si es un endpoint de agentes, registrar automáticamente
    if "/api/agents/" in str(request.url) and request.method == "POST":
        try:
            process_time = time.time() - start_time
            
            # Intentar extraer información del usuario autenticado
            user_info = extract_user_from_request(request)
            
            # Determinar el student_id
            if user_info and "email" in user_info:
                # Usar el email directamente SIN normalizar
                student_id = user_info["email"]
                student_email = user_info["email"]
                print(f"🔑 Middleware: JWT - Usuario autenticado: {student_email}")
            else:
                # Fallback al default
                student_id = "student_001"
                student_email = "unknown@example.com"
                print(f"⚠️ Middleware: Sin JWT, usando defaults: {student_email}")
            
            # Registrar interacción con más detalles
            activity = {
                "type": "agent_interaction",
                "endpoint": str(request.url.path),
                "method": request.method,
                "duration_seconds": round(process_time, 3),
                "response_status": response.status_code,
                "hour": datetime.now().hour,
                "user_email": student_email,
                "auto_tracked": True,
                # Detectar qué tipo de agente se usó
                "agent_type": request.url.path.split("/")[-1] if "/api/agents/" in str(request.url.path) else "unknown"
            }
            
            # Solo registrar si la respuesta fue exitosa
            if response.status_code == 200:
                student_stats_service.update_student_activity(student_id, activity)
                print(f"✅ Actividad registrada para {student_email}: {activity['agent_type']}")
            else:
                print(f"❌ No se registró actividad por status code: {response.status_code}")
                
        except Exception as e:
            # No interrumpir el flujo si falla el tracking
            print(f"❌ Error en tracking automático: {e}")
    
    return response

# Agentes simulados por ahora
AVAILABLE_AGENTS = {
    "exam_generator": {
        "name": "Generador de Exámenes",
        "description": "Crea exámenes personalizados basados en contenido educativo",
        "icon": "📝"
    },
    "curriculum_creator": {
        "name": "Creador de Currículum",
        "description": "Diseña planes de estudio estructurados y progresivos",
        "icon": "📚"
    },
    "tutor": {
        "name": "Tutor Personal",
        "description": "Proporciona tutoría personalizada y resolución de dudas",
        "icon": "👨‍🏫"
    },
    "lesson_planner": {
        "name": "Planificador de Lecciones",
        "description": "Diseña planes de lección detallados y actividades",
        "icon": "📋"
    },
    "performance_analyzer": {
        "name": "Analizador de Rendimiento",
        "description": "Analiza rendimiento académico y genera reportes",
        "icon": "📊"
    },
    "student_coach": {
        "name": "Coach Estudiantil IA",
        "description": "Coaching personalizado con análisis emocional avanzado",
        "icon": "🎯"
    },
    "enhanced_agent": {
        "name": "Agente Educativo Mejorado",
        "description": "Agente con respuestas garantizadas sin problemas de None",
        "icon": "🤖"
    },
    "educational_rag": {
        "name": "Biblioteca Educativa RAG",
        "description": "Búsqueda inteligente en documentos personales y recursos web",
        "icon": "📚"
    }
}

# Configuración de agentes reales
class RealAgentManager:
    def __init__(self):
        self.agents = {}
        self.setup_real_agents()
    
    def setup_real_agents(self):
        """Configurar agentes reales si están disponibles"""
        if AGENTS_AVAILABLE:
            try:
                print("🔧 Iniciando configuración de agentes reales...")
                print(f"📊 Modelo configurado: {settings.groq_model}")
                print(f"🔑 API Key presente: {'Sí' if settings.groq_api_key else 'No'}")
                
                # Debug información adicional
                debug_info = settings.get_debug_info()
                print(f"🔍 Debug Info:")
                print(f"  - API Key length: {debug_info['groq_api_key_length']}")
                print(f"  - .env en base_dir: {debug_info['env_file_exists']}")
                print(f"  - .env en parent: {debug_info['parent_env_file_exists']}")
                print(f"  - Base dir: {debug_info['base_dir']}")
                
                if not settings.verify_api_key():
                    raise ValueError("GROQ_API_KEY es requerida")
                
                self.agents = {
                    "exam_generator": ExamGeneratorAgent(settings.groq_api_key),
                    "curriculum_creator": CurriculumCreatorAgent(settings.groq_api_key),
                    "tutor": TutorAgent(settings.groq_api_key),
                    "lesson_planner": LessonPlannerAgent(settings.groq_api_key),
                    "performance_analyzer": DocumentAnalyzerAgent(settings.groq_api_key),  # Usar como analizador
                    "student_coach": StudentCoachAgent(settings.groq_api_key),  # Coach estudiantil avanzado
                    "enhanced_agent": EnhancedEducationalAgent(agent_type="enhanced", agent_name="Enhanced Educational Agent"),  # Agente mejorado
                    "educational_rag": EducationalRAGAgent(settings.groq_api_key)  # Agente RAG educativo
                }
                
                print(f"✅ {len(self.agents)} agentes reales configurados correctamente")
                print("🎯 Agentes activos:", list(self.agents.keys()))
                print(f"🤖 Modelo en uso: {settings.groq_model}")
                
            except Exception as e:
                print(f"❌ Error configurando agentes reales: {e}")
                print("📝 Cambiando a modo simulado...")
                self.agents = {}
        else:
            print("📝 Agentes no disponibles - Usando modo simulado")
            print("💡 Para usar agentes reales, instala las dependencias necesarias")
    
    async def get_agent_response(self, agent_id: str, message: str, context: dict = None) -> str:
        """Obtener respuesta de agente real o simulado"""
        if agent_id in self.agents:
            try:
                print(f"🤖 Procesando con agente REAL: {agent_id}")
                print(f"📝 Mensaje: {message[:100]}...")
                print(f"🎯 Modelo en uso: {settings.groq_model}")
                
                # Usar agente real con sistema mejorado
                agent = self.agents[agent_id]
                response = None
                
                # Usar el método mejorado dependiendo del tipo de agente
                if hasattr(agent, 'get_response'):
                    # Para agentes con método get_response mejorado
                    result = agent.get_response(message)
                    response = self._extract_clean_response(result)
                    print(f"🔍 Respuesta extraída (get_response): {type(result)} -> {len(str(response))} caracteres")
                elif hasattr(agent, 'process_specific_request'):
                    # Para agentes con método process_specific_request
                    request_data = {
                        "question": message,
                        "subject": context.get("subject", "general") if context else "general",
                        "level": context.get("level", "general") if context else "general",
                        "context": context or {}
                    }
                    result = await agent.process_specific_request(request_data)
                    response = self._extract_clean_response(result)
                    print(f"🔍 Respuesta extraída (process_specific_request): {type(result)} -> {len(str(response))} caracteres")
                else:
                    # Fallback al método original
                    result = await agent.process_request(message, context or {})
                    response = self._extract_clean_response(result)
                    print(f"🔍 Respuesta extraída (process_request): {type(result)} -> {len(str(response))} caracteres")
                
                print(f"✅ Respuesta recibida del agente {agent_id}: {len(str(response))} caracteres")
                
                # LIMPIEZA FINAL: Asegurar que no hay objetos RunResponse en el string
                final_response = self._clean_runresponse_string(response)
                print(f"🧹 Respuesta final limpia: {len(str(final_response))} caracteres")
                
                # Validar que la respuesta no esté vacía
                if not final_response or str(final_response).strip() == "" or str(final_response) == "None":
                    print(f"⚠️ Respuesta vacía del agente {agent_id}, usando fallback")
                    return await self.simulate_agent_response(agent_id, message)
                
                return str(final_response).strip()
                    
            except Exception as e:
                print(f"❌ Error en agente real {agent_id}: {e}")
                print(f"🔄 Fallback a modo simulado para {agent_id}")
                # Fallback a simulado
                return await self.simulate_agent_response(agent_id, message)
        else:
            print(f"📝 Usando agente SIMULADO: {agent_id}")
            # Usar simulado
            return await self.simulate_agent_response(agent_id, message)
    
    def _extract_clean_response(self, result):
        """Extraer respuesta limpia del resultado del agente - SOLO EL CONTENIDO"""
        if result is None:
            return None
            
        # Logging para debugging
        print(f"🔍 Extrayendo respuesta de tipo: {type(result)}")
        
        # Si es un objeto RunOutput de Agno - extraer SOLO el content
        if hasattr(result, 'content') and hasattr(result, 'content_type'):
            content = result.content
            print(f"✅ Contenido extraído de RunOutput: {len(str(content))} caracteres")
            # IMPORTANTE: Retornar solo el string del contenido, nada más
            return str(content) if content is not None else ""
            
        # Si es un objeto RunResponse/RunOutput con content
        if hasattr(result, 'content'):
            content = result.content
            print(f"✅ Contenido extraído de objeto con content: {len(str(content))} caracteres")
            return str(content) if content is not None else ""
            
        # Si es un diccionario
        if isinstance(result, dict):
            content = (result.get('content') or 
                      result.get('response') or 
                      result.get('message') or
                      str(result))
            print(f"✅ Contenido extraído de dict: {len(str(content))} caracteres")
            return str(content)
        
        # Si es string directo
        content = str(result)
        print(f"✅ Contenido convertido a string: {len(content)} caracteres")
        
        # FILTRO ADICIONAL: Si el string contiene "RunOutput(" o "RunResponse(", extraer solo el contenido
        if "RunOutput(" in content or "RunResponse(" in content:
            print("⚠️ Detectado string con RunOutput/RunResponse, filtrando...")
            # Intentar extraer solo el contenido entre content="..." 
            import re
            # Regex mejorado para capturar contenido multi-línea
            match = re.search(r'content="([^"]*(?:\\.[^"]*)*)"', content, re.DOTALL)
            if match:
                clean_content = match.group(1)
                # Procesar escapes
                clean_content = clean_content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                print(f"🧹 Contenido filtrado con regex: {len(clean_content)} caracteres")
                return clean_content
            
            # Método alternativo: buscar content= y extraer hasta la siguiente coma o fin
            if 'content=' in content:
                try:
                    start_pattern = content.find('content=') + 8
                    # Saltar espacios y comillas
                    while start_pattern < len(content) and content[start_pattern] in ' "\'':
                        start_pattern += 1
                    
                    # Buscar el final del contenido
                    if start_pattern < len(content):
                        # Si empieza con comilla, buscar la comilla de cierre
                        if content[start_pattern-1] in '"\'':
                            quote_char = content[start_pattern-1]
                            end = content.find(quote_char, start_pattern)
                            if end > start_pattern:
                                clean_content = content[start_pattern:end]
                                clean_content = clean_content.replace('\\n', '\n').replace('\\t', '\t')
                                print(f"🧹 Contenido extraído por búsqueda manual: {len(clean_content)} caracteres")
                                return clean_content
                except Exception as e:
                    print(f"❌ Error en extracción manual: {e}")
        
        return content
    
    def _clean_runresponse_string(self, text):
        """Limpiar cualquier string que contenga RunResponse y extraer solo el contenido"""
        text_str = str(text)
        
        # Si no contiene RunResponse, procesar escapes y devolver
        if "RunResponse(" not in text_str:
            return self._process_text_escapes(text_str)
            
        print("🧹 Limpiando string que contiene RunResponse...")
        
        # Método 1: Buscar content= en diferentes formatos
        import re
        
        # Patrones para diferentes formatos de content
        patterns = [
            r"content='([^']*(?:\\'[^']*)*)'",  # content='...'
            r'content="([^"]*(?:\\"[^"]*)*)"',  # content="..."
            r"content=([^,)]+?)(?:,|\s*\))",    # content=valor hasta coma o paréntesis
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_str, re.DOTALL)
            if match:
                content = match.group(1)
                # Desescapar caracteres
                content = content.replace('\\"', '"').replace("\\'", "'")
                content = content.replace('\\n', '\n').replace('\\t', '\t')
                if len(content) > 100:  # Solo si es contenido sustancial
                    print(f"✅ Contenido extraído con regex: {len(content)} caracteres")
                    return self._process_text_escapes(content)
        
        # Método 2: Extraer por posición del content=
        try:
            for quote in ['"', "'"]:
                start_marker = f'content={quote}'
                start_idx = text_str.find(start_marker)
                if start_idx != -1:
                    start_idx += len(start_marker)
                    
                    # Buscar el final, considerando escapes
                    end_idx = start_idx
                    escape_count = 0
                    
                    while end_idx < len(text_str):
                        char = text_str[end_idx]
                        if char == '\\':
                            escape_count += 1
                        elif char == quote and escape_count % 2 == 0:
                            break
                        else:
                            escape_count = 0
                        end_idx += 1
                    
                    if end_idx < len(text_str) and end_idx > start_idx + 100:
                        content = text_str[start_idx:end_idx]
                        print(f"✅ Contenido extraído por posición: {len(content)} caracteres")
                        return self._process_text_escapes(content)
                        
        except Exception as e:
            print(f"⚠️ Error en extracción posicional: {e}")
        
        # Método 3: Heurística para contenido educativo/markdown
        try:
            lines = text_str.split('\n')
            content_lines = []
            in_content_block = False
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Detectar inicio de contenido educativo
                if (any(marker in line for marker in ['# ', '## ', '### ', 'Objetivo', 'Semana', 'Duración:', 'Plan de']) or
                    (line_clean.startswith('**') and line_clean.endswith('**')) or
                    re.match(r'^\d+\.', line_clean)):
                    in_content_block = True
                    content_lines.append(line)
                    continue
                
                # Si ya estamos en contenido, continuar agregando
                if in_content_block:
                    # Parar si encontramos metadatos obvios
                    if any(stop in line for stop in ['thinking=', 'reasoning_content=', 'messages=', 'metrics=', 'model_run_id=']):
                        break
                    
                    # Agregar línea si es contenido válido
                    if (line_clean == '' or  # Líneas vacías en contenido
                        any(marker in line for marker in ['|', '- ', '* ', '\t']) or  # Tablas, listas
                        re.match(r'^\d+', line_clean) or  # Números
                        len(line_clean) > 10):  # Líneas con contenido
                        content_lines.append(line)
                    
            if len(content_lines) > 5:  # Solo si tenemos contenido sustancial
                content = '\n'.join(content_lines).strip()
                print(f"✅ Contenido extraído por heurística: {len(content)} caracteres")
                return self._process_text_escapes(content)
                
        except Exception as e:
            print(f"⚠️ Error en heurística: {e}")
        
        # Método 4: Como último recurso, limpiar metadatos obvios pero mantener el resto
        try:
            if len(text_str) > 1000:  # Solo para textos largos
                print("🔧 Aplicando limpieza conservadora...")
                
                # Remover patrones específicos de metadatos
                cleaned = text_str
                
                # Remover RunResponse wrapper pero mantener contenido
                cleaned = re.sub(r'^RunResponse\([^)]*content=(["\'])([^"\']*)\1[^)]*\)$', r'\2', cleaned)
                
                # Remover metadatos específicos
                patterns_to_remove = [
                    r'thinking=None',
                    r'reasoning_content=None', 
                    r'messages=\[[^\]]*\]',
                    r'metrics=\{[^}]*\}',
                    r'model=[^,\s]*',
                    r'model_run_id=[^,\s]*',
                    r'agent_id=[^,\s]*',
                    r'session_id=[^,\s]*'
                ]
                
                for pattern in patterns_to_remove:
                    cleaned = re.sub(pattern, '', cleaned)
                
                # Limpiar espacios extra y caracteres extraños
                cleaned = re.sub(r'\s+', ' ', cleaned)
                cleaned = cleaned.strip()
                
                if len(cleaned) > 100 and 'content=' not in cleaned[:100]:
                    print(f"✅ Limpieza conservadora exitosa: {len(cleaned)} caracteres")
                    return self._process_text_escapes(cleaned)
                    
        except Exception as e:
            print(f"⚠️ Error en limpieza conservadora: {e}")
        
        print("⚠️ No se pudo extraer contenido limpio, devolviendo string procesado")
        return self._process_text_escapes(text_str[:1000] + "..." if len(text_str) > 1000 else text_str)
    
    def _process_text_escapes(self, text):
        """Procesar escapes de texto para mostrar correctamente en frontend"""
        if not text:
            return text
            
        text_str = str(text)
        
        # Convertir escapes comunes a formato real
        processed = text_str.replace('\\n', '\n')  # Saltos de línea
        processed = processed.replace('\\t', '\t')  # Tabs
        processed = processed.replace('\\"', '"')   # Comillas escapadas
        processed = processed.replace("\\'", "'")   # Comillas simples escapadas
        processed = processed.replace('\\\\', '\\') # Barras invertidas
        
        # Limpiar caracteres de control extraños
        processed = processed.replace('\\r', '\r')
        
        # Si el texto aún tiene \n como string literal, convertirlos
        if '\\n' in processed:
            processed = processed.replace('\\n', '\n')
        
        print(f"📝 Texto procesado: {len(processed)} caracteres, contiene saltos de línea reales: {'True' if chr(10) in processed else 'False'}")
        
        return processed.strip()
    
    async def simulate_agent_response(self, agent_id: str, message: str) -> str:
        """Respuesta simulada para fallback"""
        return f"🔄 **{AVAILABLE_AGENTS.get(agent_id, {}).get('name', 'Agente')} (Modo Simulado)**\n\nHe procesado tu mensaje: '{message}'\n\n*Nota: Los agentes reales no están disponibles en este momento. Usando respuestas simuladas.*"

# Instanciar el manager de agentes
agent_manager = RealAgentManager()

# NOTA: La ruta "/" ya está definida arriba para servir el frontend/export.
# Para la información de API usamos ahora "/api" para evitar conflictos que rompen el reload.
@app.get("/api")
async def api_root():
    """Información básica de la API sin interferir con el frontend exportado"""
    return {
        "message": "Sistema Educativo Multiagente API",
        "version": "1.0.0",
        "status": "active",
        "agents": list(AVAILABLE_AGENTS.keys()),
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

# Salud extendida (mantener /health simple ya definido arriba)
@app.get("/health/full")
async def health_check_full():
    """Verificación de salud extendida del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "active",
            "agents": "active"
        }
    }

# === ENDPOINTS DE AGENTES ===

@app.get("/api/agents/test")
async def test_agents_endpoint():
    """Endpoint de prueba para verificar agentes"""
    try:
        if AGENTS_AVAILABLE:
            # Probar cada agente real
            results = {}
            for agent_id in agent_manager.agents:
                try:
                    agent = agent_manager.agents[agent_id]
                    response = await agent.process_request("¿Cuál es la capital de Francia?", {})
                    results[agent_id] = {
                        "success": True,
                        "response_sample": str(response)[:100] + "...",
                        "type": str(type(response))
                    }
                except Exception as e:
                    results[agent_id] = {
                        "success": False,
                        "error": str(e)
                    }
            return {
                "success": True,
                "agents_tested": len(results),
                "results": results
            }
        else:
            return {"success": False, "message": "Agentes no disponibles en este momento"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}/test")
async def test_specific_agent(agent_id: str):
    """Probar un agente específico"""
    try:
        if agent_id in agent_manager.agents:
            agent = agent_manager.agents[agent_id]
            response = await agent.process_request("¿Cuál es la capital de Francia?", {})
            return {
                "success": True,
                "agent_id": agent_id,
                "response_sample": str(response)[:100] + "...",
                "type": str(type(response))
            }
        else:
            return {"success": False, "message": "Agente no encontrado"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/agents/chat/formatted")
async def formatted_agent_chat(request_data: dict):
    """Chat con agente individual con respuesta formateada para frontend"""
    try:
        message = request_data.get("message", "")
        agent_id = request_data.get("agent_id", "tutor")
        context = request_data.get("context", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Mensaje requerido")
        
        if agent_id not in AVAILABLE_AGENTS:
            raise HTTPException(status_code=400, detail="Agente no válido")
        
        # Obtener respuesta del agente
        agent_response = await agent_manager.get_agent_response(agent_id, message, context)
        
        # Validación adicional: Asegurar que la respuesta es string limpio
        if hasattr(agent_response, 'content'):
            print(f"⚠️ Detectado objeto RunResponse en chat formateado para {agent_id}, extrayendo contenido...")
            agent_response = agent_manager._extract_clean_response(agent_response)
        
        # LIMPIEZA FINAL: Eliminar cualquier rastro de RunResponse
        clean_response = agent_manager._clean_runresponse_string(agent_response)
        clean_response = str(clean_response).strip()
        print(f"✅ Respuesta FINAL completamente limpia para chat formateado {agent_id}: {len(clean_response)} caracteres")
        
        agent_info = AVAILABLE_AGENTS[agent_id]
        is_real_agent = agent_id in agent_manager.agents
        
        # Formatear respuesta para el frontend
        formatted_response = {
            "success": True,
            "agent": {
                "id": agent_id,
                "name": agent_info["name"],
                "icon": agent_info["icon"],
                "description": agent_info["description"],
                "is_real": is_real_agent,
                "status": "🤖 Agente Real" if is_real_agent else "📝 Modo Simulado"
            },
            "interaction": {
                "user_message": message,
                "agent_response": clean_response,
                "formatted_content": clean_response,  # Contenido procesado para mostrar
                "raw_content": agent_response if hasattr(agent_response, 'content') else None,  # Contenido raw para debugging
                "response_length": len(clean_response),
                "contains_markdown": "##" in clean_response or "**" in clean_response or "*" in clean_response,
                "has_real_newlines": '\n' in clean_response,
                "preview": clean_response[:200] + "..." if len(clean_response) > 200 else clean_response
            },
            "metadata": {
                "model_used": settings.groq_model if is_real_agent else "simulado",
                "response_time": datetime.now().isoformat(),
                "agent_type": "real" if is_real_agent else "simulated",
                "context_provided": bool(context)
            }
        }
        
        return formatted_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/unified-chat")
async def unified_chat(request_data: dict):
    """Chat unificado con múltiples agentes - CON TRACKING DE ACTIVIDADES REALES"""
    try:
        message = request_data.get("message", "")
        # Aceptar ambos formatos de parámetros para compatibilidad
        selected_agents = request_data.get("selected_agents") or request_data.get("selectedAgents", [])
        chat_mode = request_data.get("chat_mode") or request_data.get("chatMode", "individual")
        
        # Extraer student_id del request directo o del contexto, priorizando el email
        context = request_data.get("context", {})
        student_id = (
            context.get("user_email") or  # Priorizar el email del usuario
            request_data.get("student_id") or 
            context.get("student_id") or 
            context.get("user_id") or 
            "student_001"
        )
        
        print(f"🔑 Unified chat - Student ID detectado: {student_id}")
        
        if not message:
            raise HTTPException(status_code=400, detail="Mensaje requerido")
        
        if not selected_agents:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un agente")
        
        start_time = datetime.now()
        responses = []
        total_points = 0
        
        for agent_id in selected_agents:
            if agent_id not in AVAILABLE_AGENTS:
                continue
                
            agent_info = AVAILABLE_AGENTS[agent_id]
            
            # Usar agente real en lugar de simulado
            agent_response = await agent_manager.get_agent_response(
                agent_id, 
                message, 
                {"chat_mode": chat_mode}
            )
            
            # Validación adicional: Asegurar que la respuesta es string limpio
            if hasattr(agent_response, 'content'):
                print(f"⚠️ Detectado objeto RunResponse en respuesta de {agent_id}, extrayendo contenido...")
                agent_response = agent_manager._extract_clean_response(agent_response)
            
            # LIMPIEZA FINAL: Eliminar cualquier rastro de RunResponse
            clean_response = agent_manager._clean_runresponse_string(agent_response)
            clean_response = str(clean_response).strip()
            print(f"✅ Respuesta FINAL completamente limpia para {agent_id}: {len(clean_response)} caracteres")
            
            # Determinar si es real o simulado
            is_real_agent = agent_id in agent_manager.agents
            status_indicator = "🤖 (Real)" if is_real_agent else "📝 (Simulado)"
            
            # Calcular puntos para esta interacción
            interaction_points = _calculate_points_for_interaction(agent_id, message)
            total_points += interaction_points
            
            responses.append({
                "agent_type": agent_id,
                "agent_name": f"{agent_info['name']} {status_indicator}",
                "agent_icon": agent_info["icon"],
                "response": clean_response,  # Usar respuesta limpia garantizada
                "formatted_content": clean_response,  # Para compatibilidad con frontend
                "is_real_agent": is_real_agent,
                "points_earned": interaction_points,
                "response_metadata": {
                    "length": len(clean_response),
                    "has_markdown": "##" in clean_response or "**" in clean_response,
                    "has_real_newlines": '\n' in clean_response,
                    "model_used": settings.groq_model if is_real_agent else "simulado",
                    "content_type": "clean_string",
                    "preview": clean_response[:150] + "..." if len(clean_response) > 150 else clean_response
                },
                "timestamp": datetime.now().isoformat()
            })
        
        # Calcular duración total
        end_time = datetime.now()
        total_duration = max(1, int((end_time - start_time).total_seconds() / 60))
        
        # REGISTRAR ACTIVIDAD DE CHAT
        activity = {
            "type": "chat_session",
            "subtype": "unified_chat",
            "chat_mode": chat_mode,
            "agents_used": selected_agents,
            "subject": _get_subject_from_agent(selected_agents[0] if selected_agents else "general"),
            "message": message[:100],  # Primeros 100 caracteres
            "duration_minutes": total_duration,
            "points_earned": total_points,
            "hour": start_time.hour,
            "agents_count": len(selected_agents),
            "is_multi_agent": len(selected_agents) > 1,
            "user_email": student_id  # Incluir el email del usuario para mejor tracking
        }
        
        student_stats_service.update_student_activity(student_id, activity)
        
        return {
            "success": True,
            "message": message,
            "chat_mode": chat_mode,
            "responses": responses,
            "activity_logged": True,
            "total_points_earned": total_points,
            "duration_minutes": total_duration,
            "student_id": student_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/student-coach/get-guidance")
async def get_student_guidance(request_data: dict):
    """Obtener guía del coach estudiantil usando agente real.

    Acepta múltiples formas de payload para compatibilidad:
    - {"studentData": {...}, "question": "..."}
    - {"student_id": "123", "context": {...}, "request_type": "personalized_guidance"}
    - {"studentId": "123", ...}
    """
    try:
        print(f"🏃‍♂️ Coach endpoint called with data: {request_data}")
        
        # Normalizar datos del estudiante
        student_data = request_data.get("studentData") or request_data.get("student_data") or {}
        student_id = request_data.get("student_id") or request_data.get("studentId") or student_data.get("id")
        if not student_data and student_id:
            # Construir estructura mínima si solo llega el ID
            student_data = {"id": student_id}

        context = request_data.get("context") or {}

        # Determinar la pregunta / tema de orientación
        question = (
            request_data.get("question")
            or context.get("question")
            or context.get("message")
            or "¿Cómo puedo mejorar mi rendimiento académico?"
        )
        
        print(f"🏃‍♂️ Coach question: {question}")
        print(f"🏃‍♂️ Student data: {student_data}")

        # Usar coach real si está registrado
        if "student_coach" in agent_manager.agents:
            print(f"🏃‍♂️ Using real coach agent")
            coach = agent_manager.agents["student_coach"]
            result = await coach.coach_student(question, student_data)
            print(f"🏃‍♂️ Raw coach result type: {type(result)}, length: {len(str(result))}")
            print(f"🏃‍♂️ Raw coach result preview: {str(result)[:200]}...")
            
            guidance = agent_manager._extract_clean_response(result)
            print(f"🏃‍♂️ Extracted guidance length: {len(str(guidance))}")
            print(f"🏃‍♂️ Extracted guidance preview: {str(guidance)[:200]}...")
            
            # Guardar sesión en la base de datos
            try:
                coaching_db = await get_coaching_db_service()
                session_data = {
                    'student_id': student_id or student_data.get("id", "unknown"),
                    'student_name': student_data.get("name", "Unknown"),
                    'student_message': question,
                    'coach_response': str(guidance),
                    'emotional_state': 'neutral',  # Por ahora neutral, después podemos añadir análisis emocional
                    'metadata': {
                        'agent_used': 'student_coach',
                        'model_used': settings.groq_model,
                        'response_length': len(str(guidance)),
                        'has_markdown': "##" in str(guidance) or "**" in str(guidance),
                        'context': context
                    },
                    'intervention_needed': False  # Por ahora false, después podemos añadir lógica de intervención
                }
                
                session_id = await coaching_db.save_coaching_session(session_data)
                print(f"💾 Sesión de coaching guardada en DB: {session_id}")
                
            except Exception as db_error:
                print(f"⚠️ Error guardando sesión en DB (continuando): {db_error}")
                # No fallar el endpoint si la base de datos falla
            
            agent_used = "student_coach"
        else:
            print(f"🏃‍♂️ Using tutor fallback")
            fallback_context = {"student_data": student_data, "guidance_mode": True, **context}
            guidance = await agent_manager.get_agent_response("tutor", question, fallback_context)
            agent_used = "tutor"

        # Asegurar un string limpio
        guidance_str = str(guidance)
        
        print(f"🏃‍♂️ Final guidance length: {len(guidance_str)}")

        return {
            "success": True,
            "guidance": guidance_str,
            "formatted_content": guidance_str,
            "student_id": student_id or student_data.get("id", "unknown"),
            "agent_used": agent_used,
            "is_real_agent": agent_used == "student_coach",
            "response_metadata": {
                "length": len(guidance_str),
                "has_markdown": "##" in guidance_str or "**" in guidance_str,
                "model_used": settings.groq_model
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        # Log básico para diagnosticar sin romper respuesta
        print(f"❌ Error en get_student_guidance: {e}\nPayload recibido: {request_data}")
        raise HTTPException(status_code=500, detail=str(e))

# Alias sin prefijo /api para cuando NEXT_PUBLIC_API_URL no incluye /api
@app.post("/agents/student-coach/get-guidance")
async def get_student_guidance_alias(request_data: dict):
    return await get_student_guidance(request_data)

@app.post("/api/students/interactions")
async def log_student_interaction(request_data: dict):
    """Registrar interacción del estudiante"""
    try:
        interaction_data = {
            "id": str(uuid.uuid4()),
            "student_id": request_data.get("studentId", "unknown"),
            "action": request_data.get("action", "unknown"),
            "details": request_data.get("details", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        # En una implementación real, aquí guardarías en la base de datos
        print(f"📝 Interacción registrada: {interaction_data}")
        
        return {
            "success": True,
            "interaction_id": interaction_data["id"],
            "message": "Interacción registrada exitosamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students/{student_id}/coaching-history")
async def get_student_coaching_history(student_id: str, limit: int = 50):
    """Obtener historial de coaching de un estudiante"""
    try:
        coaching_db = await get_coaching_db_service()
        history = await coaching_db.get_student_coaching_history(student_id, limit)
        
        return {
            "success": True,
            "student_id": student_id,
            "sessions": history,
            "total_sessions": len(history)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo historial de coaching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students/{student_id}/stats")
async def get_student_stats(student_id: str):
    """Obtener estadísticas de un estudiante"""
    try:
        coaching_db = await get_coaching_db_service()
        stats = await coaching_db.get_student_stats(student_id)
        
        if not stats:
            return {
                "success": True,
                "student_id": student_id,
                "stats": None,
                "message": "No se encontraron estadísticas para este estudiante"
            }
        
        return {
            "success": True,
            "student_id": student_id,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas del estudiante: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coaching/analytics")
async def get_coaching_analytics():
    """Obtener analytics generales del sistema de coaching"""
    try:
        coaching_db = await get_coaching_db_service()
        analytics = await coaching_db.get_coaching_analytics()
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo analytics de coaching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Alias para compatibilidad con frontend
@app.post("/students/interactions")
async def log_student_interaction_alias(request_data: dict):
    """Alias para registrar interacción del estudiante"""
    return await log_student_interaction(request_data)

@app.post("/api/agents/recommendations/generate")
async def generate_recommendations(request_data: dict):
    """Generar recomendaciones usando agente analizador real"""
    try:
        student_data = request_data.get("studentData", {})
        
        # Usar el analizador de rendimiento real
        analysis_prompt = f"""
        Analiza el perfil del estudiante y genera recomendaciones específicas:
        
        Datos del estudiante: {json.dumps(student_data, indent=2)}
        
        Proporciona recomendaciones estructuradas en las siguientes categorías:
        - Métodos de estudio
        - Participación y engagement
        - Colaboración
        - Gestión del tiempo
        - Recursos adicionales
        """
        
        context = {
            "student_data": student_data,
            "analysis_type": "recommendations"
        }
        
        analysis_response = await agent_manager.get_agent_response(
            "performance_analyzer", 
            analysis_prompt, 
            context
        )
        
        # Generar recomendaciones estructuradas basadas en el análisis
        recommendations = [
            {
                "id": "rec_ai_1",
                "title": "Análisis Personalizado IA",
                "description": "Recomendaciones generadas por IA basadas en tu perfil",
                "priority": "high",
                "category": "ai_analysis",
                "icon": "🤖",
                "details": analysis_response
            },
            {
                "id": "rec_2", 
                "title": "Participa más en clase",
                "description": "Hacer preguntas y participar activamente mejora el aprendizaje",
                "priority": "medium",
                "category": "engagement",
                "icon": "🙋‍♂️"
            },
            {
                "id": "rec_3",
                "title": "Forma un grupo de estudio",
                "description": "Estudiar con compañeros puede aclarar conceptos difíciles",
                "priority": "medium",
                "category": "collaboration",
                "icon": "👥"
            }
        ]
        
        return {
            "success": True,
            "recommendations": recommendations,
            "student_id": student_data.get("id", "unknown"),
            "agent_used": "performance_analyzer",
            "is_real_agent": "performance_analyzer" in agent_manager.agents,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students/{student_name}/realtime")
async def get_student_realtime_data(student_name: str):
    """Obtener datos en tiempo real del estudiante"""
    try:
        # Simular datos en tiempo real
        realtime_data = {
            "student_name": student_name,
            "online_status": "active",
            "current_activity": "Estudiando Matemáticas",
            "progress_today": {
                "lessons_completed": 3,
                "exercises_done": 12,
                "time_studied": "2h 30m"
            },
            "recent_achievements": [
                "Completó lección de Álgebra",
                "Obtuvo 95% en quiz de Geometría"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return realtime_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Nuevos endpoints que necesita el frontend

@app.post("/api/agents/analytics/analyze")
async def analyze_student_performance(request_data: dict):
    """Analizar rendimiento estudiantil usando agente real"""
    try:
        student_id = request_data.get("student_id", "unknown")
        performance_data = request_data.get("performance_data", {})
        
        analysis_prompt = f"""
        Analiza el rendimiento académico del estudiante:
        
        ID del estudiante: {student_id}
        Datos de rendimiento: {json.dumps(performance_data, indent=2)}
        
        Proporciona un análisis detallado que incluya:
        - Fortalezas identificadas
        - Áreas de mejora
        - Patrones de aprendizaje
        - Recomendaciones específicas
        """
        
        analysis = await agent_manager.get_agent_response(
            "performance_analyzer", 
            analysis_prompt,
            {"student_id": student_id, "performance_data": performance_data}
        )
        
        return {
            "success": True,
            "analysis": analysis,
            "student_id": student_id,
            "agent_used": "performance_analyzer",
            "is_real_agent": "performance_analyzer" in agent_manager.agents,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Alias para compatibilidad con frontend  
@app.post("/agents/analytics/analyze")
async def analyze_student_performance_alias(request_data: dict):
    """Alias para analizar rendimiento estudiantil"""
    return await analyze_student_performance(request_data)

@app.post("/api/agents/lesson-planner/create-plan")
async def create_study_plan(request_data: dict):
    """Crear plan de estudio usando agente planificador real"""
    try:
        student_id = request_data.get("student_id", "unknown")
        subjects = request_data.get("subjects", [])
        goals = request_data.get("learning_goals", {})
        duration = request_data.get("duration", "1_month")
        
        planning_prompt = f"""
        Crea un plan de estudio personalizado:
        
        Estudiante: {student_id}
        Materias: {', '.join(subjects)}
        Objetivos: {json.dumps(goals, indent=2)}
        Duración: {duration}
        
        El plan debe incluir:
        - Cronograma semanal
        - Objetivos específicos por materia
        - Actividades recomendadas
        - Métodos de evaluación
        - Recursos necesarios
        """
        
        study_plan = await agent_manager.get_agent_response(
            "lesson_planner",
            planning_prompt,
            {
                "student_id": student_id,
                "subjects": subjects,
                "goals": goals,
                "duration": duration
            }
        )
        
        return {
            "success": True,
            "study_plan": study_plan,
            "student_id": student_id,
            "agent_used": "lesson_planner",
            "is_real_agent": "lesson_planner" in agent_manager.agents,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/exam-generator/create-exam")
async def create_practice_exam(request_data: dict):
    """Crear examen de práctica usando agente generador real"""
    try:
        student_id = request_data.get("student_id", "unknown")
        subject = request_data.get("subject", "Matemáticas")
        difficulty = request_data.get("difficulty", "intermediate")
        question_count = request_data.get("question_count", 10)
        
        exam_prompt = f"""
        Genera un examen de práctica:
        
        Materia: {subject}
        Dificultad: {difficulty}
        Número de preguntas: {question_count}
        Estudiante: {student_id}
        
        El examen debe incluir:
        - Preguntas variadas (opción múltiple, verdadero/falso, desarrollo)
        - Respuestas correctas
        - Explicaciones detalladas
        - Tiempo estimado
        - Criterios de evaluación
        """
        
        exam = await agent_manager.get_agent_response(
            "exam_generator",
            exam_prompt,
            {
                "student_id": student_id,
                "subject": subject,
                "difficulty": difficulty,
                "question_count": question_count
            }
        )
        
        return {
            "success": True,
            "exam": exam,
            "student_id": student_id,
            "subject": subject,
            "agent_used": "exam_generator",
            "is_real_agent": "exam_generator" in agent_manager.agents,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/tutor/start-session")
async def start_tutoring_session(request_data: dict):
    """Iniciar sesión de tutoría usando agente tutor real"""
    try:
        student_id = request_data.get("student_id", "unknown")
        subject = request_data.get("subject", "General")
        questions = request_data.get("questions", [])
        
        tutoring_prompt = f"""
        Inicia una sesión de tutoría personalizada:
        
        Estudiante: {student_id}
        Materia: {subject}
        Preguntas del estudiante: {'; '.join(questions)}
        
        Como tutor personal:
        - Responde de manera clara y adaptada al nivel
        - Proporciona ejemplos prácticos
        - Sugiere ejercicios adicionales
        - Mantén un tono motivador
        - Identifica conceptos que necesitan refuerzo
        """
        
        session = await agent_manager.get_agent_response(
            "tutor",
            tutoring_prompt,
            {
                "student_id": student_id,
                "subject": subject,
                "questions": questions,
                "session_type": "interactive"
            }
        )
        
        return {
            "success": True,
            "session_data": session,
            "student_id": student_id,
            "subject": subject,
            "agent_used": "tutor",
            "is_real_agent": "tutor" in agent_manager.agents,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE ESTADÍSTICAS DEL ESTUDIANTE ===

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client = None
def _get_redis():
    if os.getenv("DISABLE_REDIS_CACHE", "false").lower() == "true":
        return None
    if redis is None:
        return None
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client

@app.get("/api/students/{student_id}/dashboard-stats")
async def get_dashboard_stats(student_id: str = "student_001"):
    """
    Obtiene estadísticas completas del dashboard del estudiante
    
    Args:
        student_id: ID del estudiante o email
        
    Returns:
        Estadísticas completas del dashboard incluyendo progreso, actividades, logros, etc.
    """
    try:
        # URL decode el student_id en caso de que sea un email
        import urllib.parse
        decoded_student_id = urllib.parse.unquote(student_id)
        
        r = _get_redis()
        key = f"dashboard_stats:{decoded_student_id}"
        if r:
            cached = r.get(key)
            if cached:
                import json as _json
                data = _json.loads(cached)
                data["success"] = True
                data["student_id"] = decoded_student_id
                data["timestamp"] = datetime.now().isoformat()
                data["cache"] = True
                return JSONResponse(content=data)

        # Intentar obtener estadísticas reales del servicio
        try:
            # Normalizar el ID usando la misma función que el tracking
            service_id = normalize_student_id(decoded_student_id)
                
            dashboard_stats = student_stats_service.get_dashboard_stats(service_id)
            
            # Asegurarse de que el email original esté incluido en la respuesta
            if "student" in dashboard_stats and "@" in decoded_student_id:
                dashboard_stats["student"]["email"] = decoded_student_id
                dashboard_stats["student"]["id"] = decoded_student_id
                
            dashboard_stats["success"] = True
            dashboard_stats["student_id"] = decoded_student_id
            dashboard_stats["timestamp"] = datetime.now().isoformat()
            dashboard_stats["cache"] = False
            
            # Cache the result
            if r:
                import json as _json
                try:
                    r.set(key, _json.dumps(dashboard_stats), ex=random.randint(60,120))
                except Exception:
                    pass
            return JSONResponse(content=dashboard_stats)
            
        except Exception as service_error:
            print(f"Error en servicio de estadísticas: {service_error}")
            # Fallback to mock data if service fails
            
        # Crear estadísticas simuladas por ahora para evitar errores del servicio
        mock_dashboard_stats = {
            "student": {
                "name": "Usuario",
                "email": decoded_student_id if "@" in decoded_student_id else f"{decoded_student_id}@example.com",
                "id": decoded_student_id,
                "total_points": 850,
                "level": 5,
                "progress_percentage": 72
            },
            "total_assignments": 12,
            "completed_assignments": 8,
            "pending_assignments": 4,
            "average_score": 87.5,
            "recent_activities": [
                {"type": "assignment_completed", "title": "Matemáticas - Álgebra", "date": "2024-08-24", "score": 95},
                {"type": "quiz_taken", "title": "Historia Universal", "date": "2024-08-23", "score": 82},
                {"type": "assignment_submitted", "title": "Literatura Española", "date": "2024-08-22", "score": 88}
            ],
            "upcoming_deadlines": [
                {"type": "assignment", "title": "Proyecto de Ciencias", "due_date": "2024-08-30"},
                {"type": "exam", "title": "Examen de Matemáticas", "due_date": "2024-09-02"}
            ],
            "achievements": [
                {"title": "Estudiante Destacado", "date": "2024-08-20"},
                {"title": "Participación Activa", "date": "2024-08-15"}
            ],
            "study_streak": {"current": 7, "longest": 15},
            "course_progress": [
                {"course": "Matemáticas", "progress": 75, "grade": "A-"},
                {"course": "Historia", "progress": 60, "grade": "B+"},
                {"course": "Literatura", "progress": 85, "grade": "A"}
            ]
        }
        
        # Usar las estadísticas simuladas en lugar del servicio que puede fallar
        dashboard_stats = mock_dashboard_stats
        dashboard_stats["success"] = True
        dashboard_stats["student_id"] = decoded_student_id
        dashboard_stats["timestamp"] = datetime.now().isoformat()
        dashboard_stats["cache"] = False
        if r:
            import json as _json
            try:
                r.set(key, _json.dumps(dashboard_stats), ex=random.randint(60,120))
            except Exception:
                pass
        return JSONResponse(content=dashboard_stats)
    except Exception as e:
        print(f"Error obteniendo estadísticas del dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# ===== HEALTH / DIAGNOSTICS =====
@app.get("/health/db")
async def health_db():
    """Verificar conexión a la base de datos y existencia de tabla users.
    Devuelve status, driver, url segura y latencia.
    """
    try:
        from auth import users_db  # type: ignore
    except ImportError:
        try:
            from src.auth import users_db  # fallback
        except ImportError as e:  # pragma: no cover
            return {"status": "down", "error": f"users_db import failed: {e}"}
    engine = users_db.engine
    start = datetime.now()
    try:
        from sqlalchemy import inspect
        with engine.connect() as conn:
            insp = inspect(conn)
            users_exists = 'users' in insp.get_table_names()
            conn.exec_driver_sql("SELECT 1")
        elapsed = (datetime.now() - start).total_seconds() * 1000
        url_obj = engine.url
        safe_url = f"{url_obj.host}/{url_obj.database}" if url_obj.host else url_obj.database
        return {
            "status": "up",
            "driver": engine.dialect.name,
            "url": safe_url,
            "users_table": users_exists,
            "time_ms": round(elapsed, 2)
        }
    except Exception as e:  # pragma: no cover
        return {"status": "down", "error": str(e)}


@app.get("/api/students/{student_id}/progress")
async def get_student_progress(student_id: str, period: str = "week"):
    """Endpoint especializado para el apartado 'Mi Progreso'.

    Combina estadísticas reales de actividades con derivaciones AI ligeras.
    """
    try:
        base_stats = student_stats_service.get_student_stats(student_id)
        subject_stats = student_stats_service._get_subject_stats(student_id)  # internal call
        trends = student_stats_service._get_trends(student_id)
        badges = student_stats_service._get_student_badges(student_id)
        recent_achievements = student_stats_service._get_recent_achievements(student_id)

        # Cargar actividades para cálculo de tendencias por materia
        activities_file = student_stats_service.activities_file
        recent_by_subject = {}
        previous_by_subject = {}
        try:
            with open(activities_file, 'r', encoding='utf-8') as f:
                all_acts = json.load(f)
            acts = all_acts.get(student_id, [])
            now = datetime.now()
            week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')
            two_weeks_ago = (now - timedelta(days=14)).strftime('%Y-%m-%d')
            for a in acts:
                subj = a.get('subject', 'General')
                date_str = a.get('date') or a.get('timestamp', '')[:10]
                if not date_str:
                    continue
                if date_str >= week_ago:
                    recent_by_subject[subj] = recent_by_subject.get(subj, 0) + 1
                elif two_weeks_ago <= date_str < week_ago:
                    previous_by_subject[subj] = previous_by_subject.get(subj, 0) + 1
        except Exception as e:
            print(f"No se pudieron cargar actividades para tendencias: {e}")

        # Añadir trend heurístico por materia
        for s in subject_stats:
            subj = s.get('subject', 'General')
            recent_c = recent_by_subject.get(subj, 0)
            prev_c = previous_by_subject.get(subj, 0)
            if recent_c > prev_c:
                s['trend'] = 'up'
            elif recent_c < prev_c:
                s['trend'] = 'down'
            else:
                s['trend'] = 'stable'

        # Construir sesiones simuladas coherentes a partir de tendencias + materias
        study_sessions = []
        today = datetime.now()
        for i, subj in enumerate(subject_stats[:7]):
            day = today - timedelta(days=i)
            study_sessions.append({
                "date": day.strftime("%Y-%m-%d"),
                "subject": subj["subject"],
                "duration": int((subj.get("time_spent_hours", 1) * 60) / max(len(subject_stats), 1)),
                "performance": min(100, int(subj.get("progress", 50) + (i * 2)))
            })
        study_sessions = list(reversed(study_sessions))

        # Calcular métricas agregadas para UI
        overall_progress = base_stats.get("overall_progress", 0)
        avg_grade = 0.0
        if subject_stats:
            avg_grade = round(sum(s.get("grade", 0) for s in subject_stats) / len(subject_stats), 1)

        total_time = round(sum(s.get("time_spent_hours", 0) for s in subject_stats), 1)
        exercises = sum(s.get("exercises_completed", 0) for s in subject_stats)

        payload = {
            "success": True,
            "student_id": student_id,
            "period": period,
            "summary": {
                "overall_progress": overall_progress,
                "average_grade": avg_grade,
                "total_study_hours": total_time,
                "exercises_completed": exercises,
                "streak_days": base_stats.get("streak_days", 0),
                "weekly_progress": base_stats.get("weekly_progress", 0)
            },
            "subjects": subject_stats,
            "sessions": study_sessions,
            "trends": trends,
            "badges": badges,
            "recent_achievements": recent_achievements,
            "generated_at": datetime.now().isoformat()
        }
        return JSONResponse(content=payload)
    except Exception as e:
        print(f"Error generando progreso: {e}")
        raise HTTPException(status_code=500, detail="Error generando progreso")

# Alias sin prefijo /api para compatibilidad cuando el frontend usa base sin /api
@app.get("/students/{student_id}/progress")
async def get_student_progress_alias(student_id: str, period: str = "week"):
    return await get_student_progress(student_id, period)


@app.get("/api/students/{student_id}/stats")
async def get_student_stats(student_id: str):
    """Obtener estadísticas completas del estudiante"""
    try:
        # Obtener todas las estadísticas del dashboard
        dashboard_stats = student_stats_service.get_dashboard_stats(student_id)
        
        return {
            "success": True,
            "student_id": student_id,
            "stats": dashboard_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/students/{student_id}/activity")
async def update_student_activity(
    student_id: str,
    activity_data: Dict[str, Any]
):
    """
    Actualiza la actividad del estudiante
    
    Args:
        student_id: ID del estudiante
        activity_data: Datos de la actividad realizada
        
    Returns:
        Confirmación de actualización
    """
    try:
        activity = activity_data.get("activity", activity_data)  # Aceptar ambos formatos
        
        # Validar campos requeridos
        if "type" not in activity:
            raise HTTPException(status_code=400, detail="El campo 'type' es requerido en la actividad")
        
        success = student_stats_service.update_student_activity(student_id, activity)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Actividad actualizada correctamente",
                "activity": activity,
                "student_id": student_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=500, detail="Error actualizando la actividad del estudiante")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error actualizando actividad del estudiante: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.post("/api/students/{student_id}/activity-log")
async def log_custom_activity(student_id: str, activity_data: dict):
    """Registrar actividad personalizada del estudiante"""
    try:
        # Validar y registrar actividad
        success = student_stats_service.update_student_activity(student_id, activity_data)
        
        if success:
            # Obtener estadísticas actualizadas
            updated_stats = student_stats_service.get_student_stats(student_id)
            
            return {
                "success": True,
                "message": "Actividad registrada exitosamente",
                "updated_stats": updated_stats,
                "activity_data": activity_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Error registrando actividad")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/students/{student_id}/recommendations")
async def get_personalized_recommendations(student_id: str = "student_001"):
    """
    Obtiene recomendaciones personalizadas para el estudiante
    
    Args:
        student_id: ID del estudiante
        
    Returns:
        Lista de recomendaciones personalizadas
    """
    try:
        dashboard_stats = student_stats_service.get_dashboard_stats(student_id)
        recommendations = dashboard_stats.get("recommendations", [])
        
        return JSONResponse(content={
            "success": True,
            "recommendations": recommendations,
            "student_id": student_id,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error obteniendo recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.get("/api/dashboard/realtime")
async def get_realtime_dashboard():
    """Obtener métricas en tiempo real del sistema"""
    try:
        # Obtener actividad reciente (últimos 5 minutos)
        # Por ahora simularemos esto, en una implementación completa
        # se obtendría de student_stats_service.get_recent_activities(minutes=5)
        
        return {
            "success": True,
            "active_students": 3,
            "total_interactions_today": 25,
            "agents_in_use": ["tutor", "exam_generator", "curriculum_creator"],
            "average_session_duration": 12.5,
            "points_distributed_today": 450,
            "most_active_subject": "Matemáticas",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test/stats-integration")
async def test_stats_integration():
    """Endpoint de prueba para verificar integración"""
    try:
        # Crear actividad de prueba
        test_activity = {
            "type": "test",
            "subject": "Test Integration",
            "duration_minutes": 1,
            "points_earned": 10,
            "test_timestamp": datetime.now().isoformat()
        }
        
        # Registrar actividad
        success = student_stats_service.update_student_activity("test_student", test_activity)
        
        # Obtener estadísticas
        stats = student_stats_service.get_dashboard_stats("test_student")
        
        return {
            "success": True,
            "integration_working": success,
            "activity_registered": success,
            "stats_available": stats is not None,
            "test_activity": test_activity,
            "test_details": stats if success else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === EDUCATIONAL RAG AGENT ENDPOINTS ===

@app.post("/api/agents/educational-rag/upload-document")
async def upload_educational_document_endpoint(request_data: dict):
    """
    Subir documento a la biblioteca educativa personal
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        content = request_data.get("content", "")
        filename = request_data.get("filename", "document.txt")
        category = request_data.get("category", "general")
        subject = request_data.get("subject", "general")
        level = request_data.get("level", "general")
        
        if not content:
            raise HTTPException(status_code=400, detail="Contenido del documento requerido")
        
        if not filename:
            raise HTTPException(status_code=400, detail="Nombre del archivo requerido")
        
        # Obtener agente
        if AGENTS_AVAILABLE and "educational_rag" in agent_manager.agents:
            rag_agent = agent_manager.agents["educational_rag"]
            result = rag_agent.upload_document(
                user_id=user_id,
                content=content,
                filename=filename,
                category=category,
                subject=subject,
                level=level
            )
        else:
            # Respuesta simulada
            result = {
                "success": True,
                "document_id": str(uuid.uuid4()),
                "message": f"Documento '{filename}' subido exitosamente (simulado)",
                "category": category,
                "subject": subject,
                "word_count": len(content.split())
            }
        
        # Registrar actividad
        activity = {
            "agent_id": "educational_rag",
            "action": "upload_document",
            "subject": "Biblioteca Educativa",
            "details": f"Subido: {filename}",
            "points": 15,
            "duration": 30
        }
        student_stats_service.update_student_activity(user_id, activity)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/educational-rag/search-documents")
async def search_educational_documents_endpoint(request_data: dict):
    """
    Buscar en documentos educativos personales
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        query = request_data.get("query", "")
        subject = request_data.get("subject")
        category = request_data.get("category")
        
        if not query:
            raise HTTPException(status_code=400, detail="Consulta de búsqueda requerida")
        
        # Obtener agente
        if AGENTS_AVAILABLE and "educational_rag" in agent_manager.agents:
            rag_agent = agent_manager.agents["educational_rag"]
            result = rag_agent.search_documents(
                user_id=user_id,
                query=query,
                subject=subject,
                category=category
            )
        else:
            # Respuesta simulada
            result = {
                "success": True,
                "documents": [
                    {
                        "id": "sim_doc_1",
                        "filename": f"Documento sobre {query}.pdf",
                        "content": f"Contenido simulado relacionado con {query}...",
                        "subject": subject or "general",
                        "category": category or "general",
                        "score": 0.8
                    }
                ],
                "total_found": 1,
                "query": query
            }
        
        # Registrar actividad
        activity = {
            "agent_id": "educational_rag",
            "action": "search_documents",
            "subject": "Biblioteca Educativa",
            "details": f"Búsqueda: {query}",
            "points": 10,
            "duration": 20
        }
        student_stats_service.update_student_activity(user_id, activity)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/educational-rag/query")
async def educational_rag_query_endpoint(request_data: dict):
    """
    Consulta educativa con RAG híbrido (documentos personales + web)
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        message = request_data.get("message", "")
        subject = request_data.get("subject")
        category = request_data.get("category")
        search_web = request_data.get("search_web", True)
        
        if not message:
            raise HTTPException(status_code=400, detail="Mensaje requerido")
        
        start_time = datetime.now()
        
        # Obtener agente
        if AGENTS_AVAILABLE and "educational_rag" in agent_manager.agents:
            rag_agent = agent_manager.agents["educational_rag"]
            
            context = {
                "user_id": user_id,
                "subject": subject,
                "category": category,
                "search_web": search_web
            }
            
            response = await rag_agent.process_request(message, context)
        else:
            # Respuesta simulada
            response = f"""
## 📚 Respuesta RAG Educativa (Simulada)

**Consulta**: {message}
{f"**Materia**: {subject}" if subject else ""}

### 📄 Desde tus documentos personales:
- No se encontraron documentos específicos (modo simulado)

### 🌐 Recursos web encontrados:
- Khan Academy: Recursos sobre {message}
- Coursera: Cursos relacionados
- Wikipedia: Artículos de referencia

### 💡 Recomendaciones:
1. Subir documentos relacionados a tu biblioteca personal
2. Especificar la materia para mejores resultados
3. Reformular la consulta con términos más específicos

---
🤖 **Tutor Educativo Premium** | 📚 Biblioteca Personal RAG (Simulado)
"""
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Registrar actividad
        activity = {
            "agent_id": "educational_rag",
            "action": "rag_query",
            "subject": subject or "Biblioteca Educativa",
            "details": f"Consulta RAG: {message[:50]}...",
            "points": 25,  # RAG queries get more points
            "duration": max(int(duration), 30)
        }
        student_stats_service.update_student_activity(user_id, activity)
        
        return {
            "success": True,
            "response": response,
            "agent_used": "educational_rag",
            "processing_time": duration,
            "context_used": {
                "subject": subject,
                "search_web": search_web,
                "user_id": user_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/health")
async def get_system_health():
    """
    Obtiene el estado de salud del sistema
    
    Returns:
        Estado actual del sistema y agentes
    """
    try:
        return JSONResponse(content={
            "status": "healthy",
            "agents_active": len(agent_manager.agents) if AGENTS_AVAILABLE else 0,
            "total_agents": len(AVAILABLE_AGENTS),
            "agents_real": AGENTS_AVAILABLE,
            "last_check": datetime.now().isoformat(),
            "services": {
                "agent_manager": "active",
                "stats_service": "active",
                "real_agents": "active" if AGENTS_AVAILABLE else "simulated"
            }
        })
    except Exception as e:
        print(f"Error obteniendo estado del sistema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.get("/api/agents/status")
async def agents_status():
    """
    Estado detallado de los agentes educativos
    """
    try:
        print(f"🔍 Agents status endpoint called - AGENTS_AVAILABLE: {AGENTS_AVAILABLE}")
        return {
            "success": True,
            "agents": list(AVAILABLE_AGENTS.keys()),
            "agents_available": AGENTS_AVAILABLE,
            "init_error": AGENTS_INIT_ERROR,
            "groq_api_key_present": bool(getattr(settings, 'groq_api_key', None)),
            "model": getattr(settings, 'groq_model', None),
            "required_env": ["GROQ_API_KEY"],
            "recommendation": None if AGENTS_AVAILABLE else "Define GROQ_API_KEY en .env y reinicia el servidor",
            "container_env": os.getenv("ENVIRONMENT", "local"),
            "deployment": "azure-container-apps" if os.getenv("ENVIRONMENT") == "production" else "local"
        }
    except Exception as e:
        print(f"❌ Error in agents_status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === EDUCATIONAL LIBRARY ENDPOINTS - REAL IMPLEMENTATION ===

@app.post("/api/library/upload")
async def upload_document_real(
    file: UploadFile = File(...),
    subject: str = Form(None),
    topic: str = Form(None)
):
    """Subir documento real a la biblioteca educativa con Azure Search"""
    try:
        if not REAL_LIBRARY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Servicio de biblioteca real no disponible")
        
        # Validar tipo de archivo
        allowed_types = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de archivo no soportado. Tipos permitidos: {', '.join(allowed_types)}"
            )
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Preparar metadata
        metadata = {}
        if subject:
            metadata['subject'] = subject
        if topic:
            metadata['topic'] = topic
        
        # Subir documento al servicio real
        result = await real_library.upload_document(
            file_content=content,
            filename=file.filename,
            content_type=file.content_type,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": "Documento subido exitosamente a Azure Search",
            "document_id": result["document_id"],
            "filename": file.filename,
            "subject": subject,
            "topic": topic,
            "size": len(content),
            "processed_content": result["processed_content"][:200] + "..." if len(result["processed_content"]) > 200 else result["processed_content"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")

@app.post("/api/library/upload-text")
async def upload_text_document(request_data: dict):
    """Subir documento de texto a la biblioteca educativa"""
    try:
        if not REAL_LIBRARY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Servicio de biblioteca real no disponible")
        
        title = request_data.get("title", "")
        content = request_data.get("content", "")
        
        if not title or not content:
            raise HTTPException(status_code=400, detail="Título y contenido son requeridos")
        
        # Crear archivo temporal para el contenido
        filename = f"{title}.txt"
        content_bytes = content.encode('utf-8')
        
        # Subir al servicio real
        result = await real_library.upload_document(
            file_content=content_bytes,
            filename=filename,
            content_type="text/plain"
        )
        
        return {
            "success": True,
            "message": "Documento de texto subido exitosamente a Azure Search",
            "document_id": result["document_id"],
            "title": title,
            "processed_content": result["processed_content"][:200] + "..." if len(result["processed_content"]) > 200 else result["processed_content"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")

@app.get("/api/library/documents")
async def get_library_documents():
    """Obtener lista de documentos reales de Azure Search"""
    try:
        if not REAL_LIBRARY_AVAILABLE:
            return {
                "success": True,
                "documents": [],
                "total_documents": 0,
                "message": "Servicio de biblioteca real no disponible",
                "timestamp": datetime.now().isoformat()
            }
        
        # Obtener documentos reales del Azure Search
        documents = await real_library.get_all_documents()
        
        return {
            "success": True,
            "documents": documents,
            "total_documents": len(documents),
            "message": f"Documentos obtenidos de Azure Search: {len(documents)}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo documentos: {str(e)}")

@app.post("/api/library/search")
async def search_library_real(request_data: dict):
    """Buscar en la biblioteca educativa real con Azure Search"""
    try:
        if not REAL_LIBRARY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Servicio de biblioteca real no disponible")
        
        query = request_data.get("query", "")
        top_k = request_data.get("top_k", 5)
        
        if not query:
            raise HTTPException(status_code=400, detail="Consulta de búsqueda requerida")
        
        # Búsqueda real con vector embeddings en Azure Search
        results = await real_library.search_documents(query, top_k=top_k)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "message": f"Búsqueda realizada en Azure Search con {len(results)} resultados",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")

@app.post("/api/library/ask")
async def ask_library_real(request_data: dict):
    """Hacer pregunta sobre documentos reales usando Educational RAG"""
    try:
        if not REAL_LIBRARY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Servicio de biblioteca real no disponible")
        
        question = request_data.get("question", "")
        
        if not question:
            raise HTTPException(status_code=400, detail="Pregunta requerida")
        
        # Usar Educational RAG Agent para responder con contexto real de Azure Search
        answer = await real_library.ask_question(question)
        
        return {
            "success": True,
            "question": question,
            "answer": answer["answer"],
            "sources": answer.get("sources", []),
            "confidence": answer.get("confidence", 0.0),
            "message": "Respuesta generada usando RAG con Azure Search",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando pregunta: {str(e)}")

@app.get("/api/library/stats")
async def get_library_stats_real():
    """Obtener estadísticas reales de Azure Search"""
    try:
        if not REAL_LIBRARY_AVAILABLE:
            return {
                "success": True,
                "total_documents": 0,
                "documents_by_subject": {},
                "documents_by_type": {"PDF": 0, "DOCX": 0, "TXT": 0},
                "total_storage": "0 MB",
                "recent_uploads": [],
                "usage_stats": {
                    "total_searches": 0,
                    "total_questions": 0,
                    "most_searched_subject": "",
                    "avg_questions_per_day": 0
                },
                "popular_searches": [],
                "popular_tags": [],
                "message": "Servicio de biblioteca real no disponible",
                "timestamp": datetime.now().isoformat()
            }
        
        # Obtener estadísticas reales del índice de Azure Search
        stats = await real_library.get_library_stats()
        
        return {
            "success": True,
            **stats,
            "message": "Estadísticas obtenidas de Azure Search",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

# === ASSIGNMENT SYSTEM (BÁSICO) ===

try:
    from src.auth.google_auth import require_teacher, get_current_user  # preferred explicit path
except ImportError:  # fallback if PYTHONPATH adjusted differently
    from auth.google_auth import require_teacher, get_current_user

@app.post("/api/assignments")
async def create_assignment(request_data: dict, current_user=Depends(require_teacher)):
    try:
        # Asegurar que se registra el teacher_id desde el token si no viene
        if "teacher_id" not in request_data:
            request_data["teacher_id"] = current_user.get("sub")
        item = assignment_service.create_assignment(request_data)
        return {"success": True, "assignment": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments")
async def list_assignments(teacher_id: str | None = None):
    try:
        items = assignment_service.list_assignments(teacher_id=teacher_id)
        return {"success": True, "assignments": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments/{assignment_id}")
async def get_assignment(assignment_id: str):
    item = assignment_service.get_assignment(assignment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"success": True, "assignment": item}

@app.post("/api/assignments/{assignment_id}/submit")
async def submit_assignment(assignment_id: str, request_data: dict):
    student_id = request_data.get("student_id") or request_data.get("studentId")
    content = request_data.get("content", "")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id requerido")
    sub = assignment_service.submit(assignment_id, student_id, content)
    # Registrar actividad en stats
    activity = {
        "type": "assignment_submission",
        "subject": assignment_service.get_assignment(assignment_id).get("subject", "General"),
        "duration_minutes": 0,
        "points_earned": 15,
        "timestamp": datetime.now().isoformat()
    }
    student_stats_service.update_student_activity(student_id, activity)
    return {"success": True, "submission": sub}

@app.get("/api/assignments/{assignment_id}/submissions")
async def list_submissions(assignment_id: str):
    subs = assignment_service.list_submissions(assignment_id)
    return {"success": True, "submissions": subs, "total": len(subs)}

@app.post("/api/submissions/{submission_id}/grade")
async def grade_submission(submission_id: str, request_data: dict, current_user=Depends(require_teacher)):
    grade = request_data.get("grade")
    feedback = request_data.get("feedback", "")
    if grade is None:
        raise HTTPException(status_code=400, detail="grade requerido")
    updated = assignment_service.grade_submission(submission_id, float(grade), feedback)
    if not updated:
        raise HTTPException(status_code=404, detail="Submission no encontrada")
    return {"success": True, "submission": updated}

@app.get("/api/students/{student_id}/assignments")
async def list_assignments_for_student(student_id: str):
    items = assignment_service.list_assignments_for_student(student_id)
    return {"success": True, "assignments": items, "total": len(items)}

@app.post("/api/assignments/{assignment_id}/status")
async def update_assignment_status(assignment_id: str, request_data: dict, current_user=Depends(require_teacher)):
    status = request_data.get("status")
    if status not in {"active", "closed", "archived"}:
        raise HTTPException(status_code=400, detail="status inválido")
    updated = assignment_service.update_assignment_status(assignment_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Assignment no encontrada")
    return {"success": True, "assignment": updated}


if __name__ == "__main__":
    # Crear directorios necesarios
    try:
        settings.create_directories()
    except:
        pass
async def upload_document_to_library(request_data: dict):
    """Subir documento a la biblioteca educativa"""
    try:
        title = request_data.get("title", "")
        content = request_data.get("content", "")
        subject = request_data.get("subject", "General")
        document_type = request_data.get("type", "pdf")
        tags = request_data.get("tags", [])
        student_id = request_data.get("student_id", "student_001")
        
        if not title or not content:
            raise HTTPException(status_code=400, detail="Título y contenido son requeridos")
        
        # Usar el agente RAG educativo para procesar el documento
        if "educational_rag" in agent_manager.agents:
            rag_agent = agent_manager.agents["educational_rag"]
            
            # Procesar el documento con el agente RAG
            if hasattr(rag_agent, 'add_document'):
                result = await rag_agent.add_document(title, content, {
                    "subject": subject,
                    "type": document_type,
                    "tags": tags,
                    "student_id": student_id
                })
            else:
                # Fallback usando método genérico
                upload_prompt = f"""
                Procesa este documento para la biblioteca educativa:
                
                Título: {title}
                Materia: {subject}
                Tipo: {document_type}
                Contenido: {content[:500]}...
                
                Extrae conceptos clave, temas principales y crea un resumen.
                """
                result = await agent_manager.get_agent_response("educational_rag", upload_prompt)
        else:
            result = f"Documento '{title}' procesado exitosamente (modo simulado)"
        
        # Simular almacenamiento del documento
        document_id = f"doc_{int(time.time())}"
        
        # Registrar actividad
        activity = {
            "type": "library_upload",
            "document_title": title,
            "subject": subject,
            "document_type": document_type,
            "points_earned": 15,
            "tags": tags
        }
        student_stats_service.update_student_activity(student_id, activity)
        
        return {
            "success": True,
            "document_id": document_id,
            "title": title,
            "subject": subject,
            "processing_result": result,
            "message": "Documento subido exitosamente a la biblioteca",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/library/search")
async def search_library_documents(request_data: dict):
    """Buscar documentos en la biblioteca educativa"""
    try:
        query = request_data.get("query", "")
        subject = request_data.get("subject", "")
        document_type = request_data.get("type", "")
        student_id = request_data.get("student_id", "student_001")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query de búsqueda requerido")
        
        # Usar el agente RAG educativo para buscar
        if "educational_rag" in agent_manager.agents:
            rag_agent = agent_manager.agents["educational_rag"]
            
            if hasattr(rag_agent, 'search_documents'):
                results = await rag_agent.search_documents(query, {
                    "subject": subject,
                    "type": document_type,
                    "student_id": student_id
                })
            else:
                search_prompt = f"""
                Busca en la biblioteca educativa documentos relacionados con:
                
                Consulta: {query}
                Materia: {subject if subject else "Cualquiera"}
                Tipo: {document_type if document_type else "Cualquiera"}
                
                Proporciona resultados relevantes con resúmenes.
                """
                results = await agent_manager.get_agent_response("educational_rag", search_prompt)
        else:
            results = f"Resultados de búsqueda para '{query}' (modo simulado)"
        
        # Registrar actividad de búsqueda
        activity = {
            "type": "library_search",
            "query": query,
            "subject": subject,
            "points_earned": 5,
            "results_found": len(mock_results)
        }
        student_stats_service.update_student_activity(student_id, activity)
        
        return {
            "success": True,
            "query": query,
            "results": mock_results,
            "ai_analysis": results,
            "total_results": len(mock_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/library/ask")
async def ask_question_about_documents(request_data: dict):
    """Hacer pregunta sobre documentos de la biblioteca"""
    try:
        question = request_data.get("question", "")
        document_ids = request_data.get("document_ids", [])
        context = request_data.get("context", {})
        student_id = request_data.get("student_id", "student_001")
        
        if not question:
            raise HTTPException(status_code=400, detail="Pregunta requerida")
        
        # Usar el agente RAG educativo para responder
        if "educational_rag" in agent_manager.agents:
            rag_agent = agent_manager.agents["educational_rag"]
            
            if hasattr(rag_agent, 'query_documents'):
                answer = await rag_agent.query_documents(question, {
                    "document_ids": document_ids,
                    "context": context,
                    "student_id": student_id
                })
            else:
                qa_prompt = f"""
                Responde esta pregunta basándote en los documentos de la biblioteca:
                
                Pregunta: {question}
                Documentos referenciados: {document_ids}
                Contexto adicional: {context}
                
                Proporciona una respuesta completa y educativa.
                """
                answer = await agent_manager.get_agent_response("educational_rag", qa_prompt)
        else:
            answer = f"Respuesta a '{question}' basada en documentos (modo simulado)"
        
        # Limpiar respuesta si es necesario
        clean_answer = agent_manager._clean_runresponse_string(answer)
        
        # Registrar actividad
        activity = {
            "type": "library_question",
            "question": question[:100],
            "documents_used": len(document_ids),
            "points_earned": 20,
            "subject": context.get("subject", "General")
        }
        student_stats_service.update_student_activity(student_id, activity)
        
        return {
            "success": True,
            "question": question,
            "answer": clean_answer,
            "document_ids": document_ids,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/library/stats")
async def get_library_stats(student_id: str = "student_001"):
    """Obtener estadísticas de la biblioteca educativa"""
    try:
        # Simular estadísticas de biblioteca
        stats = {
            "total_documents": 15,
            "documents_by_subject": {
                "Matemáticas": 5,
                "Historia": 3,
                "Ciencias": 4,
                "Literatura": 2,
                "General": 1
            },
            "documents_by_type": {
                "PDF": 8,
                "Documento": 4,
                "Presentación": 2,
                "Video": 1
            },
            "recent_uploads": [
                {
                    "title": "Ecuaciones Diferenciales",
                    "subject": "Matemáticas",
                    "date": "2024-01-10"
                },
                {
                    "title": "Revolución Francesa",
                    "subject": "Historia", 
                    "date": "2024-01-09"
                }
            ],
            "usage_stats": {
                "total_searches": 45,
                "total_questions": 32,
                "most_searched_subject": "Matemáticas",
                "avg_questions_per_day": 3.2
            },
            "popular_tags": [
                {"tag": "matemáticas", "count": 12},
                {"tag": "historia", "count": 8},
                {"tag": "ciencias", "count": 6}
            ]
        }
        
        return {
            "success": True,
            "student_id": student_id,
            "library_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/library/documents")
async def get_all_library_documents(
    student_id: str = "student_001",
    subject: str = "",
    limit: int = 20
):
    """Obtener lista de documentos de la biblioteca"""
    try:
        # Simular lista de documentos
        documents = [
            {
                "id": "doc_001",
                "title": "Introducción al Cálculo",
                "subject": "Matemáticas",
                "type": "PDF",
                "upload_date": "2024-01-10",
                "size": "2.3 MB",
                "tags": ["cálculo", "matemáticas", "derivadas"],
                "summary": "Conceptos fundamentales de cálculo diferencial e integral"
            },
            {
                "id": "doc_002",
                "title": "Historia de la Segunda Guerra Mundial",
                "subject": "Historia",
                "type": "Documento",
                "upload_date": "2024-01-09",
                "size": "1.8 MB", 
                "tags": ["historia", "guerra", "siglo-xx"],
                "summary": "Análisis detallado de los eventos de 1939-1945"
            },
            {
                "id": "doc_003",
                "title": "Química Orgánica Básica",
                "subject": "Ciencias",
                "type": "PDF",
                "upload_date": "2024-01-08",
                "size": "3.1 MB",
                "tags": ["química", "orgánica", "moléculas"],
                "summary": "Fundamentos de la química de compuestos orgánicos"
            }
        ]
        
        # Filtrar por materia si se especifica
        if subject:
            documents = [doc for doc in documents if doc["subject"].lower() == subject.lower()]
        
        # Limitar resultados
        documents = documents[:limit]
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents),
            "student_id": student_id,
            "filters": {"subject": subject} if subject else {},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== ENHANCED LIBRARY ENDPOINTS =====

@app.post("/api/library/upload/enhanced")
async def upload_document_enhanced(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(False),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    """Upload document with enhanced processing capabilities including OCR"""
    try:
        if not enhanced_library:
            # Fallback to regular library service
            if REAL_LIBRARY_AVAILABLE:
                result = await real_library.upload_document(file)
                return JSONResponse(content=result)
            else:
                raise HTTPException(status_code=503, detail="Enhanced library service not available")
        
        # Use enhanced library service
        contents = await file.read()
        result = await enhanced_library.upload_document(
            file=file,
            file_content=contents,
            ocr_enabled=ocr_enabled,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        return JSONResponse(content={
            "success": True,
            "document_id": result["document_id"],
            "title": result["title"],
            "chunks": result.get("chunks", 0),
            "file_type": result.get("file_type"),
            "ocr_performed": result.get("ocr_performed", False),
            "metadata": result.get("metadata", {})
        })
        
    except Exception as e:
        print(f"❌ Error in enhanced upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/library/upload/multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    ocr_enabled: bool = Form(False),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    """Upload multiple documents at once"""
    try:
        if not enhanced_library:
            raise HTTPException(status_code=503, detail="Enhanced library service not available")
        
        results = []
        errors = []
        
        for file in files:
            try:
                contents = await file.read()
                result = await enhanced_library.upload_document(
                    file=file,
                    file_content=contents,
                    ocr_enabled=ocr_enabled,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                results.append({
                    "filename": file.filename,
                    "document_id": result["document_id"],
                    "success": True
                })
            except Exception as file_error:
                errors.append({
                    "filename": file.filename,
                    "error": str(file_error)
                })
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "uploaded": results,
            "errors": errors,
            "total": len(files),
            "successful": len(results)
        })
        
    except Exception as e:
        print(f"❌ Error in multiple upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/library/upload/url")
async def upload_from_url(request_data: dict):
    """Upload document from URL"""
    try:
        url = request_data.get("url")
        ocr_enabled = request_data.get("ocr_enabled", False)
        
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        if not enhanced_library:
            raise HTTPException(status_code=503, detail="Enhanced library service not available")
        
        result = await enhanced_library.upload_from_url(
            url=url,
            ocr_enabled=ocr_enabled
        )
        
        return JSONResponse(content={
            "success": True,
            "document_id": result["document_id"],
            "title": result["title"],
            "source_url": url
        })
        
    except Exception as e:
        print(f"❌ Error in URL upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/library/formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    if enhanced_library:
        formats = enhanced_library.get_supported_formats()
    else:
        formats = ["pdf", "txt", "docx"]  # Default formats
    
    return JSONResponse(content={
        "formats": formats,
        "categories": {
            "documents": ["pdf", "doc", "docx", "txt", "rtf", "odt"],
            "spreadsheets": ["xls", "xlsx", "csv", "ods"],
            "presentations": ["ppt", "pptx", "odp"],
            "images": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "tiff"],
            "code": ["py", "js", "ts", "jsx", "tsx", "html", "css", "json", "xml"]
        }
    })

@app.get("/api/library/documents")
async def get_all_documents():
    """Get all documents in library"""
    try:
        if enhanced_library:
            documents = await enhanced_library.get_all_documents()
        elif REAL_LIBRARY_AVAILABLE:
            documents = real_library.documents
        else:
            documents = []
        
        return JSONResponse(content={
            "success": True,
            "documents": documents,
            "total": len(documents)
        })
        
    except Exception as e:
        print(f"❌ Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/library/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from library"""
    try:
        if enhanced_library:
            result = await enhanced_library.delete_document(document_id)
        elif REAL_LIBRARY_AVAILABLE:
            # Fallback to regular library
            real_library.documents = [d for d in real_library.documents if d.get("id") != document_id]
            result = {"success": True}
        else:
            raise HTTPException(status_code=503, detail="Library service not available")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"❌ Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/library/document/{document_id}")
async def get_document(document_id: str):
    """Get specific document details"""
    try:
        if enhanced_library:
            document = await enhanced_library.get_document(document_id)
        elif REAL_LIBRARY_AVAILABLE:
            document = next((d for d in real_library.documents if d.get("id") == document_id), None)
        else:
            document = None
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return JSONResponse(content={
            "success": True,
            "document": document
        })
        
    except Exception as e:
        print(f"❌ Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/library/document/{document_id}/ask")
async def ask_specific_document(document_id: str, request_data: dict):
    """Hacer pregunta enfocada a un documento específico.

    Estrategia: recuperar el documento (o snippet) y pasar su contenido como contexto al agente RAG
    para forzar que priorice esa fuente.
    """
    try:
        if not REAL_LIBRARY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Servicio de biblioteca real no disponible")

        question = request_data.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Pregunta requerida")

        # Obtener documento
        if enhanced_library:
            document = await enhanced_library.get_document(document_id)
        else:
            document = next((d for d in getattr(real_library, 'documents', []) if d.get("id") == document_id), None)

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        # Construir contexto manual priorizando este documento
        doc_content = document.get("content") or document.get("text") or document.get("raw_text") or ""
        context_prefix = f"Contenido del documento '{document.get('title','Sin título')}' (ID {document_id}):\n\n{doc_content[:4000]}\n\n"

        # Pasar pregunta al motor existente (ask_question) con refuerzo de contexto
        # Si real_library.ask_question permite contexto adicional, usarlo; si no, pre-pend la pregunta
        enriched_question = context_prefix + "Pregunta: " + question

        answer = await real_library.ask_question(enriched_question)

        return {
            "success": True,
            "document_id": document_id,
            "question": question,
            "answer": answer.get("answer") if isinstance(answer, dict) else answer,
            "sources": answer.get("sources", []) if isinstance(answer, dict) else [],
            "focused": True,
            "message": "Respuesta generada enfocando el documento solicitado",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error preguntando documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando pregunta focalizada: {str(e)}")
