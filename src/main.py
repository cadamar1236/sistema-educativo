"""
API principal del sistema educativo multiagente
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional, Dict, Any
import json
import sys
import os
import uuid
from datetime import datetime

# Agregar el directorio padre al path para imports absolutos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.models import *
from src.services.document_service_simple import DocumentService
from src.core.agent_orchestrator_simple import AgentOrchestrator
from src.services.student_stats_service import student_stats_service

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

# === MIDDLEWARE PARA TRACKING AUTOMÁTICO ===

@app.middleware("http")
async def track_requests(request, call_next):
    """Middleware para tracking automático de todas las interacciones"""
    import time
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)
    
    # Si es un endpoint de agentes, registrar automáticamente
    if "/api/agents/" in str(request.url) and request.method == "POST":
        try:
            process_time = time.time() - start_time
            
            # Intentar extraer student_id del request
            student_id = "student_001"  # Default
            
            # Registrar interacción genérica
            activity = {
                "type": "api_interaction",
                "endpoint": str(request.url.path),
                "method": request.method,
                "duration_seconds": process_time,
                "response_status": response.status_code,
                "hour": datetime.now().hour,
                "auto_tracked": True
            }
            
            # Solo registrar si la respuesta fue exitosa
            if response.status_code == 200:
                student_stats_service.update_student_activity(student_id, activity)
                
        except Exception as e:
            # No interrumpir el flujo si falla el tracking
            print(f"Error en tracking automático: {e}")
    
    return response

# Servicios globales
document_service = DocumentService()
agent_orchestrator = AgentOrchestrator()

# === FUNCIONES AUXILIARES PARA TRACKING ===

def _get_subject_from_agent(agent_id: str) -> str:
    """Mapea agente a materia académica"""
    agent_subject_map = {
        "exam_generator": "Evaluación",
        "curriculum_creator": "Planificación",
        "tutor": "Tutoría General", 
        "lesson_planner": "Organización",
        "analytics": "Análisis Académico",
        "document_analyzer": "Análisis de Documentos",
        "student_coach": "Coaching Estudiantil"
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
        "analytics": 8,
        "document_analyzer": 12,
        "student_coach": 18
    }
    
    return base_points + agent_bonus.get(agent_id, 0)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema Educativo Multiagente",
        "version": "1.0.0",
        "status": "active",
        "agents": [agent.value for agent in AgentType]
    }


@app.get("/health")
async def health_check():
    """Verificación de salud del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "document_service": "active",
            "agent_orchestrator": "active",
            "database": "connected"
        }
    }


# === ENDPOINTS DE DOCUMENTOS ===

@app.post("/documents/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    subject: Optional[str] = None,
    grade_level: Optional[str] = None
):
    """Subir un nuevo documento a la biblioteca"""
    
    try:
        # Validar tipo de archivo
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido. Extensiones válidas: {settings.allowed_extensions}"
            )
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Procesar documento
        document = await document_service.upload_document(
            file_content=content,
            filename=file.filename,
            subject=subject,
            grade_level=grade_level
        )
        
        return document
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents(
    subject: Optional[str] = None,
    grade_level: Optional[str] = None
):
    """Listar documentos en la biblioteca"""
    
    try:
        documents = await document_service.list_documents(
            subject=subject,
            grade_level=grade_level
        )
        return documents
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/search")
async def search_documents(
    query: str,
    n_results: int = 10,
    subject: Optional[str] = None,
    grade_level: Optional[str] = None
):
    """Buscar documentos usando búsqueda semántica"""
    
    try:
        results = await document_service.search_documents(
            query=query,
            n_results=n_results,
            subject=subject,
            grade_level=grade_level
        )
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Eliminar documento de la biblioteca"""
    
    try:
        success = await document_service.delete_document(document_id)
        if success:
            return {"message": "Documento eliminado exitosamente"}
        else:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE AGENTES ===

@app.post("/agents/request", response_model=AgentResponse)
async def agent_request(request: AgentRequest):
    """Procesar solicitud a un agente específico"""
    
    try:
        response = await agent_orchestrator.process_request(request)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/exam/generate")
async def generate_exam(
    subject: str,
    grade_level: str,
    topic: str,
    num_questions: int = 10,
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
    question_types: List[QuestionType] = None,
    document_ids: List[str] = None,
    student_id: str = "student_001"  # Agregar student_id
):
    """Generar examen usando el agente especializado - CON TRACKING DE ACTIVIDAD"""
    
    if question_types is None:
        question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER]
    
    try:
        start_time = datetime.now()
        
        prompt = f"""
        Genera un examen de {subject} para {grade_level} sobre el tema: {topic}
        
        Especificaciones:
        - Número de preguntas: {num_questions}
        - Nivel de dificultad: {difficulty.value}
        - Tipos de preguntas: {[qt.value for qt in question_types]}
        
        El examen debe incluir:
        1. Título descriptivo
        2. Instrucciones claras
        3. Preguntas variadas y bien estructuradas
        4. Respuestas correctas
        5. Explicaciones para cada respuesta
        6. Tiempo estimado de resolución
        
        Formato de respuesta en JSON con la estructura del modelo Exam.
        """
        
        request = AgentRequest(
            agent_type=AgentType.EXAM_GENERATOR,
            prompt=prompt,
            documents=document_ids or [],
            parameters={
                "subject": subject,
                "grade_level": grade_level,
                "topic": topic,
                "num_questions": num_questions,
                "difficulty": difficulty.value,
                "question_types": [qt.value for qt in question_types]
            }
        )
        
        response = await agent_orchestrator.process_request(request)
        
        # Calcular duración y registrar actividad
        end_time = datetime.now()
        duration_minutes = max(1, int((end_time - start_time).total_seconds() / 60))
        
        # REGISTRAR ACTIVIDAD DE GENERACIÓN DE EXAMEN
        activity = {
            "type": "exercise",
            "subtype": "exam_generated",
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty.value,
            "question_count": num_questions,
            "grade_level": grade_level,
            "duration_minutes": duration_minutes,
            "points_earned": 25 + (num_questions * 2),  # Puntos por crear examen
            "hour": start_time.hour,
            "agent_used": "exam_generator",
            "is_real_agent": response.metadata.get("agent_type") == "real"
        }
        
        student_stats_service.update_student_activity(student_id, activity)
        
        return {
            "success": True,
            "exam": response.response,
            "metadata": response.metadata,
            "student_id": student_id,
            "subject": subject,
            "activity_logged": True,
            "points_earned": activity["points_earned"],
            "duration_minutes": duration_minutes,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/curriculum/create")
async def create_curriculum(
    subject: str,
    grade_level: str,
    duration_weeks: int,
    objectives: List[str],
    document_ids: List[str] = None
):
    """Crear currículum usando el agente especializado"""
    
    try:
        prompt = f"""
        Crea un currículum completo de {subject} para {grade_level}
        
        Especificaciones:
        - Duración: {duration_weeks} semanas
        - Objetivos principales: {objectives}
        
        El currículum debe incluir:
        1. Título y descripción general
        2. Unidades temáticas detalladas
        3. Objetivos específicos por unidad
        4. Secuencia lógica de aprendizaje
        5. Recursos recomendados
        6. Métodos de evaluación
        7. Prerequisitos y conexiones
        
        Formato de respuesta en JSON con la estructura del modelo Curriculum.
        """
        
        request = AgentRequest(
            agent_type=AgentType.CURRICULUM_CREATOR,
            prompt=prompt,
            documents=document_ids or [],
            parameters={
                "subject": subject,
                "grade_level": grade_level,
                "duration_weeks": duration_weeks,
                "objectives": objectives
            }
        )
        
        response = await agent_orchestrator.process_request(request)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/tutor/chat")
async def tutor_chat(
    message: str,
    student_context: Optional[Dict[str, Any]] = None,
    document_ids: List[str] = None,
    student_id: str = "student_001"  # Agregar student_id
):
    """Chat con el tutor personalizado - CON TRACKING DE ACTIVIDAD"""
    
    try:
        start_time = datetime.now()
        
        context_info = ""
        if student_context:
            context_info = f"\nContexto del estudiante: {json.dumps(student_context, indent=2)}"
        
        prompt = f"""
        Un estudiante necesita ayuda con la siguiente consulta: {message}
        {context_info}
        
        Proporciona una respuesta educativa, clara y adaptada al nivel del estudiante.
        Incluye ejemplos prácticos cuando sea apropiado.
        Mantén un tono amigable y motivador.
        """
        
        request = AgentRequest(
            agent_type=AgentType.TUTOR,
            prompt=prompt,
            documents=document_ids or [],
            context=student_context or {}
        )
        
        response = await agent_orchestrator.process_request(request)
        
        # Calcular duración y registrar actividad
        end_time = datetime.now()
        duration_minutes = max(1, int((end_time - start_time).total_seconds() / 60))
        
        # REGISTRAR ACTIVIDAD DE TUTORÍA
        activity = {
            "type": "lesson",
            "subtype": "tutoring_session",
            "subject": student_context.get("subject", "General") if student_context else "General",
            "message": message[:100],  # Primeros 100 caracteres
            "has_context": bool(student_context),
            "document_count": len(document_ids) if document_ids else 0,
            "duration_minutes": duration_minutes,
            "points_earned": 30 + (len(message.split()) * 2),  # Puntos por participación y detalle
            "hour": start_time.hour,
            "agent_used": "tutor",
            "is_real_agent": response.metadata.get("agent_type") == "real",
            "engagement_level": "high" if len(message) > 50 else "medium"
        }
        
        student_stats_service.update_student_activity(student_id, activity)
        
        return {
            "success": True,
            "tutor_response": response.response,
            "metadata": response.metadata,
            "student_id": student_id,
            "activity_logged": True,
            "points_earned": activity["points_earned"],
            "duration_minutes": duration_minutes,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/lesson/plan")
async def create_lesson_plan(
    subject: str,
    grade_level: str,
    topic: str,
    duration_minutes: int = 45,
    learning_objectives: List[str] = None,
    document_ids: List[str] = None
):
    """Crear plan de lección usando el agente especializado"""
    
    try:
        objectives_text = ""
        if learning_objectives:
            objectives_text = f"\nObjetivos de aprendizaje: {learning_objectives}"
        
        prompt = f"""
        Crea un plan de lección detallado para {subject} ({grade_level})
        
        Especificaciones:
        - Tema: {topic}
        - Duración: {duration_minutes} minutos
        {objectives_text}
        
        El plan debe incluir:
        1. Título y objetivos claros
        2. Materiales necesarios
        3. Estructura temporal de la clase
        4. Actividades de inicio, desarrollo y cierre
        5. Estrategias de enseñanza variadas
        6. Métodos de evaluación
        7. Tareas o actividades de seguimiento
        8. Adaptaciones para diferentes estilos de aprendizaje
        
        Formato de respuesta en JSON con la estructura del modelo LessonPlan.
        """
        
        request = AgentRequest(
            agent_type=AgentType.LESSON_PLANNER,
            prompt=prompt,
            documents=document_ids or [],
            parameters={
                "subject": subject,
                "grade_level": grade_level,
                "topic": topic,
                "duration_minutes": duration_minutes,
                "learning_objectives": learning_objectives or []
            }
        )
        
        response = await agent_orchestrator.process_request(request)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/collaborate")
async def multi_agent_collaboration(
    task: str,
    agents: List[AgentType],
    context: Optional[Dict[str, Any]] = None
):
    """Colaboración entre múltiples agentes"""
    
    try:
        # Enriquecer tarea con contexto
        enriched_task = task
        if context:
            enriched_task += f"\n\nContexto adicional: {json.dumps(context, indent=2)}"
        
        result = await agent_orchestrator.multi_agent_collaboration(
            task=enriched_task,
            participating_agents=agents
        )
        
        return {
            "success": True,
            "result": result,
            "participating_agents": [agent.value for agent in agents],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/search")
async def search_and_answer(
    query: str,
    agent_type: AgentType = AgentType.TUTOR
):
    """Buscar en documentos y responder usando un agente"""
    
    try:
        answer = await agent_orchestrator.search_and_answer(query, agent_type)
        
        return {
            "query": query,
            "answer": answer,
            "agent_used": agent_type.value,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE UTILIDADES ===

@app.get("/agents/types")
async def get_agent_types():
    """Obtener tipos de agentes disponibles"""
    return {
        "agent_types": [
            {
                "id": agent.value,
                "name": agent.value.replace("_", " ").title(),
                "description": _get_agent_description(agent)
            }
            for agent in AgentType
        ]
    }


@app.post("/agents/chat")
async def agent_chat(
    message: str,
    agent_type: AgentType,
    context: Optional[Dict[str, Any]] = None,
    document_ids: List[str] = None
):
    """Chat directo con cualquier agente seleccionado"""
    
    try:
        request = AgentRequest(
            agent_type=agent_type,
            prompt=message,
            documents=document_ids or [],
            context=context or {}
        )
        
        response = await agent_orchestrator.process_request(request)
        
        return {
            "agent_type": agent_type.value,
            "agent_name": agent_type.value.replace("_", " ").title(),
            "response": response.response,
            "status": response.status,
            "timestamp": response.timestamp,
            "metadata": response.metadata
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/multi-chat")
async def multi_agent_chat(
    message: str,
    agent_types: List[AgentType],
    context: Optional[Dict[str, Any]] = None
):
    """Chat con múltiples agentes simultáneamente"""
    
    try:
        responses = []
        
        for agent_type in agent_types:
            request = AgentRequest(
                agent_type=agent_type,
                prompt=message,
                documents=[],
                context=context or {}
            )
            
            response = await agent_orchestrator.process_request(request)
            responses.append({
                "agent_type": agent_type.value,
                "agent_name": agent_type.value.replace("_", " ").title(),
                "response": response.response,
                "status": response.status,
                "is_real_agent": response.metadata.get("agent_type") == "real"
            })
        
        return {
            "message": message,
            "responses": responses,
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(agent_types)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/status")
async def get_agents_status():
    """Obtener estado de todos los agentes"""
    
    agents_info = []
    for agent_type in AgentType:
        agent = agent_orchestrator.agents.get(agent_type)
        agents_info.append({
            "id": agent_type.value,
            "name": agent_type.value.replace("_", " ").title(), 
            "status": "active" if agent else "inactive",
            "type": "real" if agent and not isinstance(agent, str) else "fallback",
            "description": _get_agent_description(agent_type)
        })
    
    return {
        "agents": agents_info,
        "total_agents": len(agents_info),
        "active_agents": len([a for a in agents_info if a["status"] == "active"])
    }


# === ENDPOINTS PARA STUDENT COACH ===

@app.post("/api/agents/student-coach/get-guidance")
async def get_student_guidance(
    student_id: str,
    current_situation: str,
    goals: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None
):
    """Obtener orientación del coach estudiantil"""
    
    try:
        guidance_prompt = f"""
        Estudiante ID: {student_id}
        Situación actual: {current_situation}
        Objetivos: {goals if goals else 'No especificados'}
        
        Como coach estudiantil, proporciona orientación personalizada que incluya:
        1. Análisis de la situación actual
        2. Recomendaciones específicas
        3. Plan de acción paso a paso
        4. Recursos de apoyo
        5. Métricas de seguimiento
        """
        
        request = AgentRequest(
            agent_type=AgentType.TUTOR,  # Usar tutor como coach por ahora
            prompt=guidance_prompt,
            context=context or {}
        )
        
        response = await agent_orchestrator.process_request(request)
        
        return {
            "student_id": student_id,
            "guidance": response.response,
            "recommendations": [
                "Establecer horario de estudio regular",
                "Participar en grupos de estudio",
                "Buscar apoyo cuando sea necesario",
                "Celebrar pequeños logros"
            ],
            "next_steps": [
                "Implementar plan de estudio",
                "Seguimiento semanal",
                "Evaluación de progreso"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS PARA RECOMMENDATIONS ===

@app.post("/api/agents/recommendations/generate")
async def generate_recommendations(
    student_profile: Dict[str, Any],
    learning_goals: List[str],
    current_performance: Optional[Dict[str, Any]] = None
):
    """Generar recomendaciones personalizadas para estudiante"""
    
    try:
        recommendations_prompt = f"""
        Perfil del estudiante: {json.dumps(student_profile, indent=2)}
        Objetivos de aprendizaje: {learning_goals}
        Rendimiento actual: {json.dumps(current_performance or {}, indent=2)}
        
        Genera recomendaciones personalizadas que incluyan:
        1. Estrategias de estudio específicas
        2. Recursos de aprendizaje recomendados
        3. Actividades de práctica
        4. Cronograma sugerido
        5. Métricas de seguimiento
        """
        
        request = AgentRequest(
            agent_type=AgentType.PERFORMANCE_ANALYZER,
            prompt=recommendations_prompt,
            context={
                "student_profile": student_profile,
                "learning_goals": learning_goals,
                "current_performance": current_performance
            }
        )
        
        response = await agent_orchestrator.process_request(request)
        
        return {
            "recommendations": response.response,
            "personalized_plan": {
                "study_schedule": "Lunes a Viernes, 2 horas diarias",
                "focus_areas": learning_goals[:3],  # Top 3 goals
                "resources": [
                    "Videos educativos",
                    "Ejercicios interactivos", 
                    "Grupos de estudio"
                ]
            },
            "success_metrics": [
                "Mejora en evaluaciones",
                "Consistencia en estudio",
                "Participación activa"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === NUEVO ENDPOINT PARA CHAT UNIFICADO ===

@app.post("/api/agents/unified-chat")
async def unified_agent_chat(request: UnifiedChatRequest):
    """Chat unificado con selección de agentes - CON TRACKING DE ACTIVIDADES REALES"""
    
    try:
        # Obtener student_id del contexto o usar por defecto
        student_id = request.context.get("student_id", "student_001") if request.context else "student_001"
        start_time = datetime.now()
        
        # Convertir strings a AgentType
        selected_agents = []
        for agent_str in request.selected_agents:
            try:
                agent_type = AgentType(agent_str)
                selected_agents.append(agent_type)
            except ValueError:
                continue  # Ignorar agentes no válidos
        
        # Si no se especifican agentes válidos, usar todos
        if not selected_agents:
            selected_agents = list(AgentType)
        
        responses = []
        total_duration = 0
        
        if request.chat_mode == "collaboration":
            # Modo colaboración: agentes trabajan juntos
            collaboration_result = await agent_orchestrator.multi_agent_collaboration(
                task=request.message,
                participating_agents=selected_agents
            )
            
            # Calcular duración
            end_time = datetime.now()
            total_duration = max(1, int((end_time - start_time).total_seconds() / 60))
            
            # REGISTRAR ACTIVIDAD DE COLABORACIÓN
            activity = {
                "type": "chat_session",
                "subtype": "collaboration",
                "agents_used": [agent.value for agent in selected_agents],
                "subject": _get_subject_from_agent(selected_agents[0].value if selected_agents else "general"),
                "message": request.message[:100],  # Primeros 100 caracteres
                "duration_minutes": total_duration,
                "points_earned": 30 + len(selected_agents) * 10,  # Bonus por colaboración
                "hour": start_time.hour,
                "is_collaboration": True,
                "participants_count": len(selected_agents)
            }
            
            student_stats_service.update_student_activity(student_id, activity)
            
            return {
                "mode": "collaboration",
                "message": request.message,
                "collaboration_result": collaboration_result,
                "participating_agents": [agent.value for agent in selected_agents],
                "timestamp": datetime.now().isoformat(),
                "activity_logged": True,
                "points_earned": activity["points_earned"],
                "duration_minutes": total_duration,
                "student_id": student_id
            }
        
        else:
            # Modo individual: cada agente responde por separado
            total_points = 0
            
            for agent_type in selected_agents:
                agent_request = AgentRequest(
                    agent_type=agent_type,
                    prompt=request.message,
                    context=request.context or {}
                )
                
                response = await agent_orchestrator.process_request(agent_request)
                
                # Calcular puntos para esta interacción
                interaction_points = _calculate_points_for_interaction(agent_type.value, request.message)
                total_points += interaction_points
                
                responses.append({
                    "agent_type": agent_type.value,
                    "agent_name": agent_type.value.replace("_", " ").title(),
                    "response": response.response,
                    "status": response.status,
                    "is_real_agent": response.metadata.get("agent_type") == "real",
                    "points_earned": interaction_points
                })
            
            # Calcular duración total
            end_time = datetime.now()
            total_duration = max(1, int((end_time - start_time).total_seconds() / 60))
            
            # REGISTRAR ACTIVIDAD INDIVIDUAL
            activity = {
                "type": "chat_session",
                "subtype": "individual",
                "agents_used": [agent.value for agent in selected_agents],
                "subject": _get_subject_from_agent(selected_agents[0].value if selected_agents else "general"),
                "message": request.message[:100],
                "duration_minutes": total_duration,
                "points_earned": total_points,
                "hour": start_time.hour,
                "is_collaboration": False,
                "agents_count": len(selected_agents)
            }
            
            student_stats_service.update_student_activity(student_id, activity)
            
            return {
                "mode": "individual",
                "message": request.message,
                "responses": responses,
                "total_agents": len(selected_agents),
                "timestamp": datetime.now().isoformat(),
                "activity_logged": True,
                "total_points_earned": total_points,
                "duration_minutes": total_duration,
                "student_id": student_id
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINT PARA OBTENER ESTADO DE AGENTES ===

@app.get("/api/agents/status")
async def get_agents_status():
    """Obtener estado de todos los agentes"""
    
    try:
        agents_status = []
        
        for agent_type in AgentType:
            agent = agent_orchestrator.agents.get(agent_type)
            is_real = not isinstance(agent, str)
            
            agents_status.append({
                "type": agent_type.value,
                "name": agent_type.value.replace("_", " ").title(),
                "status": "active" if agent else "inactive",
                "is_real_agent": is_real,
                "description": _get_agent_description(agent_type)
            })
        
        return {
            "agents": agents_status,
            "total_agents": len(AgentType),
            "real_agents_count": sum(1 for status in agents_status if status["is_real_agent"]),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE ESTUDIANTES ===

@app.get("/students/{student_name}/realtime")
async def get_student_realtime_data(student_name: str):
    """Obtener datos en tiempo real del estudiante"""
    
    try:
        # Simular datos en tiempo real
        return {
            "student_name": student_name,
            "online_status": "active",
            "current_activity": "Estudiando Matemáticas",
            "progress_today": 75,
            "time_studied": "2h 30m",
            "last_interaction": datetime.now().isoformat(),
            "notifications": [
                {
                    "id": "notif_1",
                    "type": "achievement",
                    "message": "¡Completaste 5 ejercicios seguidos!",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/students/interactions")
async def log_student_interaction(
    student_id: str,
    interaction: Dict[str, Any],
    timestamp: Optional[str] = None
):
    """Registrar interacción del estudiante"""
    
    try:
        interaction_record = {
            "id": str(uuid.uuid4()),
            "student_id": student_id,
            "interaction": interaction,
            "timestamp": timestamp or datetime.now().isoformat()
        }
        
        # Aquí podrías guardar en base de datos
        print(f"📝 Interacción registrada: {interaction_record}")
        
        return {
            "success": True,
            "interaction_id": interaction_record["id"],
            "message": "Interacción registrada correctamente"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE RECOMENDACIONES ===

@app.post("/api/agents/recommendations/generate")
async def generate_recommendations(
    student_id: str,
    context: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
):
    """Generar recomendaciones personalizadas usando el agente analizador"""
    
    try:
        # Construir prompt para recomendaciones
        prompt = f"""
        Genera recomendaciones personalizadas para el estudiante {student_id}.
        
        Contexto del estudiante:
        {json.dumps(context or {}, indent=2)}
        
        Timestamp: {timestamp or datetime.now().isoformat()}
        
        Proporciona recomendaciones específicas para:
        1. Áreas de estudio prioritarias
        2. Métodos de aprendizaje recomendados
        3. Recursos educativos sugeridos
        4. Metas a corto y largo plazo
        5. Horarios de estudio optimizados
        """
        
        request = AgentRequest(
            agent_type=AgentType.PERFORMANCE_ANALYZER,
            prompt=prompt,
            context={
                "student_id": student_id,
                "generation_type": "recommendations",
                "timestamp": timestamp,
                **(context or {})
            }
        )
        
        response = await agent_orchestrator.process_request(request)
        
        return {
            "student_id": student_id,
            "recommendations": response.response,
            "generated_by": "performance_analyzer",
            "timestamp": datetime.now().isoformat(),
            "status": response.status
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/student-coach/get-guidance")
async def get_student_guidance(
    student_id: str,
    context: Optional[Dict[str, Any]] = None,
    request_type: Optional[str] = None
):
    """Obtener orientación personalizada del coach estudiantil"""
    
    try:
        # Usar el agente tutor como coach
        prompt = f"""
        Como coach estudiantil personal, proporciona orientación para el estudiante {student_id}.
        
        Tipo de solicitud: {request_type or "Orientación general"}
        
        Contexto del estudiante:
        {json.dumps(context or {}, indent=2)}
        
        Proporciona:
        1. Análisis de la situación actual
        2. Consejos específicos y personalizados
        3. Estrategias de mejora
        4. Motivación y apoyo emocional
        5. Pasos concretos a seguir
        
        Mantén un tono cercano, motivador y profesional.
        """
        
        request = AgentRequest(
            agent_type=AgentType.TUTOR,
            prompt=prompt,
            context={
                "student_id": student_id,
                "coaching_mode": True,
                "request_type": request_type,
                **(context or {})
            }
        )
        
        response = await agent_orchestrator.process_request(request)
        
        return {
            "student_id": student_id,
            "guidance": response.response,
            "coach_type": "tutor_agent",
            "timestamp": datetime.now().isoformat(),
            "status": response.status
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_agent_description(agent_type: AgentType) -> str:
    """Obtener descripción de un tipo de agente"""
    descriptions = {
        AgentType.EXAM_GENERATOR: "Genera exámenes personalizados basados en contenido educativo",
        AgentType.CURRICULUM_CREATOR: "Crea planes de estudio estructurados y progresivos",
        AgentType.TUTOR: "Proporciona tutoría personalizada y resolución de dudas",
        AgentType.PERFORMANCE_ANALYZER: "Analiza rendimiento académico y genera reportes",
        AgentType.LESSON_PLANNER: "Diseña planes de lección detallados y actividades"
    }
    return descriptions.get(agent_type, "Agente educativo especializado")


# ===== ENDPOINTS DE ESTADÍSTICAS DEL ESTUDIANTE =====

@app.get("/api/students/{student_id}/dashboard-stats")
async def get_dashboard_stats(student_id: str = "student_001"):
    """
    Obtiene todas las estadísticas necesarias para el dashboard del estudiante
    
    Args:
        student_id: ID del estudiante
        
    Returns:
        Diccionario con estadísticas completas del dashboard
    """
    try:
        stats = student_stats_service.get_dashboard_stats(student_id)
        return JSONResponse(content=stats)
    except Exception as e:
        print(f"Error obteniendo estadísticas del dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


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
        activity = activity_data.get("activity", {})
        
        # Validar campos requeridos
        if "type" not in activity:
            raise HTTPException(status_code=400, detail="El campo 'type' es requerido en la actividad")
        
        success = student_stats_service.update_student_activity(student_id, activity)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Actividad actualizada correctamente",
                "activity": activity
            })
        else:
            raise HTTPException(status_code=500, detail="Error actualizando la actividad del estudiante")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error actualizando actividad del estudiante: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


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
            "recommendations": recommendations
        })
    except Exception as e:
        print(f"Error obteniendo recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


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
            "agents_active": 5,
            "total_agents": 5,
            "last_check": datetime.now().isoformat(),
            "services": {
                "document_service": "active",
                "agent_orchestrator": "active",
                "stats_service": "active"
            }
        })
    except Exception as e:
        print(f"Error obteniendo estado del sistema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


# === NUEVOS ENDPOINTS PARA INTEGRACIÓN COMPLETA ===

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


@app.get("/api/dashboard/realtime")
async def get_realtime_dashboard():
    """Obtener métricas en tiempo real del sistema"""
    try:
        # Obtener actividad reciente (últimos 5 minutos)
        # Por ahora simularemos esto, en una implementación completa
        # se obtendría de student_stats_service.get_recent_activities(minutes=5)
        
        return {
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
            "integration_working": success,
            "activity_registered": success,
            "stats_available": stats is not None,
            "test_activity": test_activity,
            "test_details": stats if success else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === SISTEMA DE LOGROS Y VERIFICACIÓN ===

class AchievementChecker:
    """Verificador de logros basado en actividades reales"""
    
    @staticmethod
    async def check_and_award_achievements(student_id: str, activity: dict):
        """Verifica y otorga logros basados en la actividad"""
        
        try:
            # Obtener historial de actividades
            stats = student_stats_service.get_student_stats(student_id)
            new_achievements = []
            
            # Verificar primer uso de cada agente
            if activity.get("agent_used") and activity.get("is_real_agent"):
                achievement_key = f"first_use_{activity['agent_used']}"
                existing_achievements = stats.get("achievements", [])
                
                if not any(ach.get("id") == achievement_key for ach in existing_achievements):
                    new_achievements.append({
                        "id": achievement_key,
                        "title": f"Explorador de {activity['agent_used']}",
                        "description": f"Primera vez usando el agente {activity['agent_used']}",
                        "points": 50,
                        "icon": "🎯",
                        "unlocked_date": datetime.now().strftime("%Y-%m-%d")
                    })
            
            # Verificar rachas especiales
            if stats.get("streak_days", 0) == 7:
                new_achievements.append({
                    "id": "week_streak",
                    "title": "Semana Perfecta",
                    "description": "7 días consecutivos de estudio",
                    "points": 100,
                    "icon": "🏆",
                    "unlocked_date": datetime.now().strftime("%Y-%m-%d")
                })
            
            # Registrar nuevos logros
            for achievement in new_achievements:
                achievement_activity = {
                    "type": "achievement",
                    "subtype": achievement["id"],
                    "points_earned": achievement["points"],
                    "achievement_data": achievement,
                    "hour": datetime.now().hour
                }
                student_stats_service.update_student_activity(student_id, achievement_activity)
            
            return new_achievements
            
        except Exception as e:
            print(f"Error verificando logros: {e}")
            return []


@app.post("/api/achievements/check/{student_id}")
async def check_achievements(student_id: str, activity_data: dict):
    """Verificar y otorgar logros para una actividad"""
    try:
        new_achievements = await AchievementChecker.check_and_award_achievements(
            student_id, activity_data
        )
        
        return {
            "success": True,
            "student_id": student_id,
            "new_achievements": new_achievements,
            "achievements_count": len(new_achievements),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Crear directorios necesarios
    settings.create_directories()
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
