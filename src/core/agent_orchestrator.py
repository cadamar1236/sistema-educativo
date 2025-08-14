"""
Sistema de agentes multiagente usando LangGraph y AutoGen
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Importaciones simplificadas para evitar problemas de compatibilidad
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None
    END = None

try:
    from langchain.schema import HumanMessage, AIMessage
except ImportError:
    HumanMessage = None
    AIMessage = None

try:
    import autogen
    from autogen import ConversableAgent, GroupChat, GroupChatManager
except ImportError:
    autogen = None
    ConversableAgent = None
    GroupChat = None
    GroupChatManager = None

from src.config import settings
from src.models import AgentType, AgentRequest, AgentResponse
from src.services.document_service import DocumentService


class AgentOrchestrator:
    """Orquestador principal de agentes - versión simplificada"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.agents = {}
        self._setup_basic_agents()
    
    def _setup_basic_agents(self):
        """Configurar agentes básicos sin dependencias complejas"""
        # Por ahora usaremos implementaciones simples
        self.agents = {
            AgentType.EXAM_GENERATOR: "exam_agent",
            AgentType.CURRICULUM_CREATOR: "curriculum_agent", 
            AgentType.TUTOR: "tutor_agent",
            AgentType.PERFORMANCE_ANALYZER: "analyzer_agent",
            AgentType.LESSON_PLANNER: "planner_agent"
        }
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Procesar solicitud de agente de manera simplificada"""
        try:
            # Implementación simple usando strings por ahora
            agent_name = self.agents.get(request.agent_type, "default_agent")
            
            # Simular respuesta del agente
            response_content = await self._generate_simple_response(request)
            
            return AgentResponse(
                agent_id=str(uuid.uuid4()),
                agent_type=request.agent_type,
                response=response_content,
                status="completed",
                timestamp=datetime.now(),
                metadata={
                    "agent_name": agent_name,
                    "processing_time": "1.5s"
                }
            )
        except Exception as e:
            return AgentResponse(
                agent_id=str(uuid.uuid4()),
                agent_type=request.agent_type,
                response=f"Error procesando solicitud: {str(e)}",
                status="error",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
    
    async def _generate_simple_response(self, request: AgentRequest) -> str:
        """Generar respuesta simple basada en el tipo de agente"""
        if request.agent_type == AgentType.EXAM_GENERATOR:
            return self._generate_exam_response(request)
        elif request.agent_type == AgentType.CURRICULUM_CREATOR:
            return self._generate_curriculum_response(request)
        elif request.agent_type == AgentType.TUTOR:
            return self._generate_tutor_response(request)
        elif request.agent_type == AgentType.LESSON_PLANNER:
            return self._generate_lesson_response(request)
        elif request.agent_type == AgentType.PERFORMANCE_ANALYZER:
            return self._generate_analyzer_response(request)
        else:
            return "Respuesta de agente genérico: He procesado tu solicitud."
    
    def _generate_exam_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente de exámenes"""
        params = request.parameters or {}
        subject = params.get('subject', 'Materia')
        topic = params.get('topic', 'Tema')
        num_questions = params.get('num_questions', 5)
        
        return f"""
# Examen de {subject}: {topic}

## Instrucciones
- Tiempo estimado: 45 minutos
- Lee cuidadosamente cada pregunta
- Selecciona la mejor respuesta

## Preguntas ({num_questions} preguntas)

### Pregunta 1
**¿Cuál es el concepto principal de {topic}?**
a) Opción A
b) Opción B  
c) Opción C
d) Opción D

**Respuesta correcta:** c) Opción C
**Explicación:** Esta es la respuesta correcta porque...

### Pregunta 2
**Explica brevemente la importancia de {topic} en {subject}**
_(Respuesta abierta - 3-5 líneas)_

**Respuesta modelo:** {topic} es fundamental en {subject} porque permite...

[Continúa con más preguntas...]
        """
    
    def _generate_curriculum_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente de currículum"""
        params = request.parameters or {}
        subject = params.get('subject', 'Materia')
        grade_level = params.get('grade_level', 'Nivel')
        duration = params.get('duration_weeks', 12)
        
        return f"""
# Currículum de {subject} - {grade_level}

## Información General
- **Duración:** {duration} semanas
- **Nivel:** {grade_level}
- **Materia:** {subject}

## Unidad 1: Introducción (Semanas 1-2)
**Objetivos:**
- Comprender conceptos básicos
- Establecer fundamentos

**Contenidos:**
- Tema 1.1: Conceptos fundamentales
- Tema 1.2: Principios básicos

## Unidad 2: Desarrollo (Semanas 3-6)
**Objetivos:**
- Aplicar conocimientos
- Desarrollar habilidades

**Contenidos:**
- Tema 2.1: Aplicaciones prácticas
- Tema 2.2: Ejercicios guiados

[Continúa con más unidades...]
        """
    
    def _generate_tutor_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente tutor"""
        return f"""
¡Hola! Soy tu tutor virtual y estoy aquí para ayudarte.

Respecto a tu consulta: "{request.prompt}"

Te explico paso a paso:

1. **Primero,** es importante entender que...
2. **Luego,** debemos considerar...
3. **Finalmente,** podemos concluir que...

💡 **Consejo:** Recuerda practicar estos conceptos con ejercicios.

¿Te gustaría que profundice en algún punto específico?
        """
    
    def _generate_lesson_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente planificador de lecciones"""
        params = request.parameters or {}
        subject = params.get('subject', 'Materia')
        topic = params.get('topic', 'Tema')
        duration = params.get('duration_minutes', 45)
        
        return f"""
# Plan de Lección: {topic}

## Información General
- **Materia:** {subject}
- **Tema:** {topic}
- **Duración:** {duration} minutos

## Estructura de la Clase

### Inicio (10 min)
- Saludo y repaso de la clase anterior
- Introducción al tema de hoy
- Objetivos de aprendizaje

### Desarrollo (25 min)
- Explicación del concepto principal
- Ejemplos prácticos
- Actividad interactiva

### Cierre (10 min)
- Resumen de puntos clave
- Preguntas y respuestas
- Tarea para casa

## Materiales Necesarios
- Pizarra/Presentación
- Material de apoyo
- Ejercicios prácticos
        """
    
    def _generate_analyzer_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente analizador"""
        return f"""
# Análisis de Rendimiento Académico

## Resumen Ejecutivo
He analizado los datos proporcionados y aquí están los hallazgos principales:

## Puntos Fuertes
- ✅ Buen desempeño en conceptos básicos
- ✅ Participación activa en clase
- ✅ Mejora constante en evaluaciones

## Áreas de Mejora
- 🔸 Necesita reforzar temas avanzados
- 🔸 Mejorar técnicas de estudio
- 🔸 Aumentar práctica independiente

## Recomendaciones
1. Establecer horario de estudio regular
2. Usar técnicas de repaso espaciado
3. Buscar apoyo adicional en temas difíciles

## Próximos Pasos
- Seguimiento semanal
- Evaluación continua
- Ajuste de estrategias según progreso
        """
    
    async def multi_agent_collaboration(self, task: str, participating_agents: List[AgentType]) -> str:
        """Colaboración simple entre agentes"""
        results = []
        
        for agent_type in participating_agents:
            request = AgentRequest(
                agent_type=agent_type,
                prompt=f"Colabora en esta tarea: {task}",
                parameters={}
            )
            response = await self.process_request(request)
            results.append(f"**{agent_type.value}:** {response.response[:200]}...")
        
        return "\n\n".join(results)
    
    async def search_and_answer(self, query: str, agent_type: AgentType) -> str:
        """Buscar y responder usando un agente específico"""
        # Buscar documentos relevantes
        search_results = await self.document_service.search_documents(query, n_results=3)
        
        # Crear contexto con resultados
        context = "\n".join([f"- {doc['content'][:100]}..." for doc in search_results])
        
        # Generar respuesta
        request = AgentRequest(
            agent_type=agent_type,
            prompt=f"Pregunta: {query}\n\nContexto:\n{context}",
            parameters={}
        )
        
        response = await self.process_request(request)
        return response.response
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
        
        # Agente Creador de Currículum
        self.agents[AgentType.CURRICULUM_CREATOR] = ConversableAgent(
            name="CurriculumCreator",
            system_message="""Eres un especialista en diseño curricular. Tu función es:
            1. Crear planes de estudio estructurados y progresivos
            2. Definir objetivos de aprendizaje claros
            3. Organizar contenidos de manera lógica
            4. Establecer prerequisitos y secuencias
            5. Alinear con estándares educativos
            
            Considera siempre la edad, nivel y contexto educativo.""",
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
        
        # Agente Tutor Personalizado
        self.agents[AgentType.TUTOR] = ConversableAgent(
            name="PersonalTutor",
            system_message="""Eres un tutor educativo personalizado. Tu misión es:
            1. Proporcionar explicaciones claras y adaptadas
            2. Resolver dudas específicas de estudiantes
            3. Ofrecer ejemplos prácticos y relevantes
            4. Adaptar el lenguaje al nivel del estudiante
            5. Motivar y guiar el aprendizaje
            
            Siempre sé paciente, comprensivo y alentador.""",
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
        
        # Agente Analizador de Rendimiento
        self.agents[AgentType.PERFORMANCE_ANALYZER] = ConversableAgent(
            name="PerformanceAnalyzer",
            system_message="""Eres un especialista en análisis de rendimiento académico. Tu trabajo es:
            1. Analizar datos de rendimiento estudiantil
            2. Identificar patrones y tendencias
            3. Detectar fortalezas y áreas de mejora
            4. Generar recomendaciones específicas
            5. Crear reportes comprensibles para educadores y padres
            
            Basa tus análisis en datos objetivos y proporciona insights accionables.""",
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
        
        # Agente Planificador de Clases
        self.agents[AgentType.LESSON_PLANNER] = ConversableAgent(
            name="LessonPlanner",
            system_message="""Eres un experto en planificación de lecciones. Tu función es:
            1. Crear planes de lección detallados y estructurados
            2. Diseñar actividades variadas y engaging
            3. Establecer objetivos de aprendizaje claros
            4. Sugerir recursos y materiales apropiados
            5. Incluir métodos de evaluación
            
            Adapta cada plan al nivel, materia y estilo de aprendizaje.""",
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Procesar solicitud de agente"""
        
        start_time = datetime.now()
        
        try:
            # Obtener contexto de documentos si se proporcionan
            context = await self._get_document_context(request.documents)
            
            # Crear prompt enriquecido
            enriched_prompt = await self._enrich_prompt(
                request.prompt, 
                context, 
                request.context,
                request.parameters
            )
            
            # Seleccionar y ejecutar agente
            agent = self.agents[request.agent_type]
            
            # Ejecutar con AutoGen
            response_content = await self._execute_agent(agent, enriched_prompt, request.agent_type)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                success=True,
                content=response_content,
                agent_type=request.agent_type,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                success=False,
                content=f"Error procesando solicitud: {str(e)}",
                agent_type=request.agent_type,
                processing_time=processing_time
            )
    
    async def _get_document_context(self, document_ids: Optional[List[str]]) -> str:
        """Obtener contexto de documentos"""
        
        if not document_ids:
            return ""
        
        context_parts = []
        
        for doc_id in document_ids:
            # Buscar contenido del documento
            search_results = await self.document_service.search_documents(
                query="",  # Búsqueda vacía para obtener chunks del documento
                n_results=5
            )
            
            for result in search_results:
                if result['metadata']['document_id'] == doc_id:
                    context_parts.append(result['document'])
        
        return "\n\n".join(context_parts)
    
    async def _enrich_prompt(self, prompt: str, document_context: str, 
                           user_context: Dict[str, Any], 
                           parameters: Dict[str, Any]) -> str:
        """Enriquecer prompt con contexto adicional"""
        
        enriched_parts = [prompt]
        
        if document_context:
            enriched_parts.append(f"\n\nContexto de documentos:\n{document_context}")
        
        if user_context:
            enriched_parts.append(f"\n\nContexto adicional:\n{json.dumps(user_context, indent=2)}")
        
        if parameters:
            enriched_parts.append(f"\n\nParámetros:\n{json.dumps(parameters, indent=2)}")
        
        return "\n".join(enriched_parts)
    
    async def _execute_agent(self, agent: ConversableAgent, prompt: str, 
                           agent_type: AgentType) -> str:
        """Ejecutar agente específico"""
        
        # Crear un usuario dummy para la conversación
        user_proxy = ConversableAgent(
            name="User",
            system_message="Eres un usuario que hace solicitudes a agentes educativos.",
            llm_config=False,  # No necesita LLM
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        # Iniciar conversación
        chat_result = user_proxy.initiate_chat(
            agent,
            message=prompt,
            max_turns=1,
            silent=True
        )
        
        # Extraer respuesta
        if chat_result and chat_result.chat_history:
            return chat_result.chat_history[-1]['content']
        else:
            return "No se pudo generar una respuesta."
    
    async def multi_agent_collaboration(self, task: str, 
                                      participating_agents: List[AgentType]) -> str:
        """Colaboración entre múltiples agentes usando GroupChat"""
        
        # Configuración para GroupChat
        llm_config = {
            "config_list": [{
                "model": settings.ollama_model,
                "base_url": settings.ollama_base_url,
                "api_key": "fake-key"
            }],
            "timeout": settings.agent_timeout,
        }
        
        # Seleccionar agentes participantes
        selected_agents = [self.agents[agent_type] for agent_type in participating_agents]
        
        # Crear usuario coordinador
        user_proxy = ConversableAgent(
            name="Coordinator",
            system_message="Coordinas la colaboración entre agentes educativos.",
            llm_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        # Crear GroupChat
        group_chat = GroupChat(
            agents=[user_proxy] + selected_agents,
            messages=[],
            max_round=len(participating_agents) * 2
        )
        
        # Crear manager
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config
        )
        
        # Iniciar colaboración
        chat_result = user_proxy.initiate_chat(
            manager,
            message=task,
            silent=True
        )
        
        # Compilar respuestas
        if chat_result and chat_result.chat_history:
            responses = []
            for message in chat_result.chat_history:
                if message['name'] != 'Coordinator':
                    responses.append(f"{message['name']}: {message['content']}")
            
            return "\n\n".join(responses)
        
        return "No se pudo completar la colaboración entre agentes."
    
    async def search_and_answer(self, query: str, agent_type: AgentType = AgentType.TUTOR) -> str:
        """Buscar en documentos y responder usando un agente"""
        
        # Buscar documentos relevantes
        search_results = await self.document_service.search_documents(query, n_results=5)
        
        # Compilar contexto
        context_parts = []
        for result in search_results:
            context_parts.append(result['document'])
        
        context = "\n\n".join(context_parts)
        
        # Crear solicitud
        request = AgentRequest(
            agent_type=agent_type,
            prompt=f"Basándote en el siguiente contexto, responde a la pregunta: {query}",
            context={"search_results": search_results},
            documents=[],
            parameters={}
        )
        
        # Procesar y devolver respuesta
        response = await self.process_request(request)
        return response.content
