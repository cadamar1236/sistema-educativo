"""
Servidor API Bridge para Julia Frontend
=======================================

Este servidor actúa como puente entre el frontend React/Next.js 
y el sistema multiagente educativo de Julia.

Proporciona endpoints REST que el frontend puede consumir
y traduce las llamadas a los agentes reales del backend.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import sys
import os
import uvicorn
import json
from datetime import datetime

# Agregar el directorio padre al path para importar los agentes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar los agentes reales del sistema Julia
try:
    from agents.analytics.agent import EducationalAnalyticsAgent, create_analytics_agent
    from agents.student_coach.agent import StudentCoachAgent
    from agents.lesson_planner.agent import LessonPlannerAgent
    from agents.tutor.agent import TutorAgent
    from agents.exam_generator.agent import ExamGeneratorAgent
    from agents.document_analyzer.agent import DocumentAnalyzerAgent
    from src.core.agent_coordinator import AgentCoordinator
    from src.config import load_config
except ImportError as e:
    print(f"Error importando agentes: {e}")
    print("Asegúrate de que todos los agentes estén disponibles")

# Modelos Pydantic para las requests
class StudentAnalyticsRequest(BaseModel):
    student_id: str
    performance_data: Dict[str, Any] = {}

class CoachingRequest(BaseModel):
    student_id: str
    context: Dict[str, Any]

class StudyPlanRequest(BaseModel):
    student_id: str
    subjects: List[str]
    learning_goals: Dict[str, Any]
    duration: str = "1_month"

class TutoringRequest(BaseModel):
    student_id: str
    subject: str
    questions: List[str]
    session_type: str = "interactive"

class InteractionLog(BaseModel):
    student_id: str
    interaction: Dict[str, Any]
    timestamp: str

# Crear la aplicación FastAPI
app = FastAPI(
    title="Julia Education API Bridge",
    description="API Bridge para conectar Julia Frontend con Sistema Multiagente",
    version="1.0.0"
)

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales para los agentes
agents = {}
coordinator = None
config = None

@app.on_event("startup")
async def startup_event():
    """Inicializar agentes al arrancar el servidor"""
    global agents, coordinator, config
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Inicializar agentes reales
        agents['analytics'] = await create_analytics_agent(config.groq_api_key)
        agents['coach'] = StudentCoachAgent(config.groq_api_key)
        agents['planner'] = LessonPlannerAgent(config.groq_api_key)
        agents['tutor'] = TutorAgent(config.groq_api_key)
        agents['exam'] = ExamGeneratorAgent(config.groq_api_key)
        agents['document'] = DocumentAnalyzerAgent(config.groq_api_key)
        
        # Inicializar coordinador
        coordinator = AgentCoordinator(agents)
        
        print("✅ Todos los agentes Julia inicializados correctamente")
        
    except Exception as e:
        print(f"❌ Error inicializando agentes: {e}")
        # Crear agentes mock para desarrollo
        agents = {
            'analytics': None,
            'coach': None,
            'planner': None,
            'tutor': None,
            'exam': None,
            'document': None
        }

# ================================
# ENDPOINTS PARA ANALYTICS AGENT
# ================================

@app.post("/api/agents/analytics/analyze")
async def analyze_student_performance(request: StudentAnalyticsRequest):
    """Analizar rendimiento estudiantil con el agente de analytics"""
    try:
        if agents.get('analytics'):
            # Usar agente real
            metrics = await agents['analytics'].analyze_student_performance(
                request.student_id, 
                request.performance_data
            )
            
            return {
                "success": True,
                "agent_name": "EducationalAnalyticsAgent",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "performance_score": metrics.avg_performance,
                    "engagement_score": metrics.engagement_score,
                    "learning_style": metrics.learning_style,
                    "risk_factors": metrics.risk_factors,
                    "achievements_count": len(metrics.interventions_needed),
                    "study_streak": 5,  # Ejemplo
                    "performance_trend": "improving" if metrics.avg_performance > 0.7 else "stable"
                }
            }
        else:
            # Datos de desarrollo
            return {
                "success": True,
                "agent_name": "MockAnalyticsAgent",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "performance_score": 0.78,
                    "engagement_score": 0.85,
                    "learning_style": "visual",
                    "risk_factors": [],
                    "achievements_count": 12,
                    "study_streak": 5,
                    "performance_trend": "improving"
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@app.post("/api/agents/analytics/parent-report")
async def generate_parent_report(request: StudentAnalyticsRequest):
    """Generar reporte para padres"""
    try:
        if agents.get('analytics'):
            report = await agents['analytics'].generate_parent_report(request.student_id)
            return {
                "success": True,
                "report": report,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "report": {
                    "student_name": request.student_id,
                    "summary": "Reporte en desarrollo - conectando con sistema Julia"
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

# ================================
# ENDPOINTS PARA STUDENT COACH
# ================================

@app.post("/api/agents/student-coach/get-guidance")
async def get_student_coaching(request: CoachingRequest):
    """Obtener orientación del coach estudiantil"""
    try:
        if agents.get('coach'):
            # Usar agente coach real
            guidance = await agents['coach'].provide_guidance(
                request.student_id,
                request.context
            )
            
            return {
                "success": True,
                "agent_name": "StudentCoachAgent",
                "timestamp": datetime.now().isoformat(),
                "response": guidance.get('response', 'Orientación personalizada en proceso'),
                "insights": guidance.get('insights', 'Analizando tu progreso actual'),
                "recommendations": guidance.get('recommendations', [
                    "Mantén una rutina de estudio consistente",
                    "Practica técnicas de concentración",
                    "Busca ayuda cuando la necesites"
                ]),
                "alerts": guidance.get('alerts', []),
                "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        else:
            # Respuesta de desarrollo
            return {
                "success": True,
                "agent_name": "MockCoachAgent",
                "timestamp": datetime.now().isoformat(),
                "response": f"¡Excelente progreso {request.student_id}! Continúa con tu dedicación.",
                "insights": "Tu patrón de estudio muestra consistencia y mejora gradual.",
                "recommendations": [
                    "Continúa con sesiones de estudio de 45 minutos",
                    "Incluye descansos de 10 minutos entre sesiones", 
                    "Repasa conceptos clave antes de dormir"
                ],
                "alerts": [],
                "session_id": f"mock_session_{datetime.now().strftime('%H%M%S')}"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en coaching: {str(e)}")

# ================================
# ENDPOINTS PARA LESSON PLANNER
# ================================

@app.post("/api/agents/lesson-planner/create-plan")
async def create_study_plan(request: StudyPlanRequest):
    """Crear plan de estudio personalizado"""
    try:
        if agents.get('planner'):
            plan = await agents['planner'].create_lesson_plan(
                request.subjects,
                request.learning_goals,
                request.duration
            )
            
            return {
                "success": True,
                "agent_name": "LessonPlannerAgent",
                "plan": plan,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Plan de desarrollo
            return {
                "success": True,
                "agent_name": "MockPlannerAgent",
                "plan": {
                    "title": f"Plan de Estudio para {request.student_id}",
                    "duration": request.duration,
                    "subjects": request.subjects,
                    "schedule": "Plan personalizado en desarrollo",
                    "goals": request.learning_goals
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando plan: {str(e)}")

# ================================
# ENDPOINTS PARA TUTOR AGENT
# ================================

@app.post("/api/agents/tutor/start-session")
async def start_tutoring_session(request: TutoringRequest):
    """Iniciar sesión de tutoría"""
    try:
        if agents.get('tutor'):
            session = await agents['tutor'].start_tutoring_session(
                request.student_id,
                request.subject,
                request.questions
            )
            
            return {
                "success": True,
                "agent_name": "TutorAgent",
                "session": session,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "agent_name": "MockTutorAgent",
                "session": {
                    "session_id": f"tutor_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "subject": request.subject,
                    "status": "Sesión iniciada - conectando con tutor IA",
                    "questions": request.questions
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando tutoría: {str(e)}")

# ================================
# ENDPOINTS GENERALES
# ================================

@app.post("/api/agents/recommendations/generate")
async def generate_recommendations(request: CoachingRequest):
    """Generar recomendaciones personalizadas"""
    try:
        recommendations = [
            "Dedica 30 minutos diarios a repasar conceptos clave",
            "Utiliza técnicas de mapas mentales para organizar información",
            "Practica ejercicios de concentración antes de estudiar",
            "Establece metas de estudio pequeñas y alcanzables",
            "Toma descansos regulares durante sesiones largas"
        ]
        
        return {
            "success": True,
            "recommendations": recommendations,
            "priority": "normal",
            "generated_by": "Julia AI System",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")

@app.get("/api/students/{student_id}/realtime")
async def get_student_realtime_data(student_id: str):
    """Obtener datos en tiempo real del estudiante"""
    try:
        return {
            "success": True,
            "student_id": student_id,
            "name": f"Estudiante {student_id}",
            "grade": "10° Grado",
            "status": "Activo en sistema Julia",
            "last_activity": datetime.now().isoformat(),
            "performance": 0.78,
            "engagement": 0.85,
            "connected_agents": len([a for a in agents.values() if a is not None]),
            "system_status": "operational"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos: {str(e)}")

@app.post("/api/students/interactions")
async def log_student_interaction(log: InteractionLog, background_tasks: BackgroundTasks):
    """Registrar interacción del estudiante"""
    try:
        # Agregar tarea en background para procesar la interacción
        background_tasks.add_task(process_interaction, log)
        
        return {
            "success": True,
            "message": "Interacción registrada",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando interacción: {str(e)}")

@app.post("/api/agents/coordinator/execute")
async def coordinate_agents(request: Dict[str, Any]):
    """Ejecutar coordinación de agentes"""
    try:
        if coordinator:
            result = await coordinator.execute_request(request)
            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "result": "Coordinador en desarrollo - respuesta simulada",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en coordinación: {str(e)}")

# ================================
# FUNCIONES AUXILIARES
# ================================

async def process_interaction(log: InteractionLog):
    """Procesar interacción en background"""
    try:
        print(f"📝 Procesando interacción de {log.student_id}: {log.interaction}")
        
        # Aquí puedes agregar lógica para:
        # - Actualizar métricas del estudiante
        # - Triggerar análisis de patrones
        # - Generar alertas automáticas
        # - Etc.
        
    except Exception as e:
        print(f"Error procesando interacción: {e}")

@app.get("/api/health")
async def health_check():
    """Verificar estado del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_status": {
            name: "connected" if agent else "disconnected" 
            for name, agent in agents.items()
        },
        "coordinator_status": "connected" if coordinator else "disconnected"
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Julia Education API Bridge",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# ================================
# EJECUTAR SERVIDOR
# ================================

if __name__ == "__main__":
    print("🚀 Iniciando Julia API Bridge...")
    print("📡 Conectando con sistema multiagente...")
    
    uvicorn.run(
        "api_bridge:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
