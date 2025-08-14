"""
Coordinador de agentes educativos usando Agno Framework
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

from agno.team import Team
from agno.models.groq import Groq
from agno.tools.reasoning import ReasoningTools

from src.config import settings, validate_api_keys
from src.models import AgentRequest, AgentResponse, AgentType
from src.services.document_service import DocumentService
from agents import (
    ExamGeneratorAgent,
    CurriculumCreatorAgent, 
    TutorAgent,
    LessonPlannerAgent,
    DocumentAnalyzerAgent
)


class AgentCoordinator:
    """
    Coordinador principal del sistema multiagente educativo usando Agno.
    Gestiona la comunicación, coordinación y colaboración entre agentes.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("coordinator")
        
        # Validar configuración
        if not validate_api_keys():
            raise ValueError("API keys no configuradas correctamente")
        
        # Inicializar agentes individuales
        self.agents = self._initialize_agents()
        
        # Configurar equipo de agentes usando Agno
        self.agent_team = self._create_agent_team()
        
        # Servicios auxiliares
        self.document_service = DocumentService()
        
        # Métricas y estado
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
        self.logger.info("Coordinador de agentes inicializado correctamente")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """
        Inicializa todos los agentes individuales
        """
        try:
            # Obtener API key
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY no encontrada en variables de entorno")
            
            agents = {
                AgentType.EXAM_GENERATOR: ExamGeneratorAgent(groq_api_key),
                AgentType.CURRICULUM_CREATOR: CurriculumCreatorAgent(groq_api_key),
                AgentType.TUTOR: TutorAgent(groq_api_key),
                AgentType.LESSON_PLANNER: LessonPlannerAgent(groq_api_key),
                AgentType.DOCUMENT_ANALYZER: DocumentAnalyzerAgent(groq_api_key)
            }
            
            self.logger.info(f"Inicializados {len(agents)} agentes")
            return agents
            
        except Exception as e:
            self.logger.error(f"Error inicializando agentes: {e}")
            raise
    
    def _create_agent_team(self) -> Team:
        """
        Crea un equipo coordinado de agentes usando Agno
        """
        try:
            # Extraer los agentes de Agno de cada agente personalizado
            agno_agents = []
            for agent in self.agents.values():
                if hasattr(agent, 'agent'):
                    agno_agents.append(agent.agent)
            
            # Configurar modelo coordinador
            coordinator_model = Groq(
                id=settings.groq_model,
                api_key=settings.groq_api_key
            )
            
            # Crear equipo con modo de coordinación
            team = Team(
                mode="coordinate",  # Los agentes colaboran bajo coordinación
                members=agno_agents,
                model=coordinator_model,
                success_criteria="Proporcionar respuestas educativas completas y precisas",
                instructions=[
                    "Coordina eficientemente las tareas entre agentes especializados",
                    "Asegúrate de que las respuestas sean coherentes y complementarias",
                    "Utiliza el agente más apropiado para cada tipo de tarea",
                    "Combina las fortalezas de múltiples agentes cuando sea beneficioso"
                ],
                show_tool_calls=settings.debug,
                markdown=True
            )
            
            self.logger.info("Equipo de agentes creado exitosamente")
            return team
            
        except Exception as e:
            self.logger.error(f"Error creando equipo de agentes: {e}")
            # Retornar None si no se puede crear el equipo
            return None
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Procesa una solicitud dirigiéndola al agente apropiado
        
        Args:
            request: Solicitud del usuario
            
        Returns:
            Respuesta del agente correspondiente
        """
        start_time = datetime.now()
        
        try:
            self.metrics["total_requests"] += 1
            
            # Obtener el agente apropiado
            agent = self.agents.get(request.agent_type)
            if not agent:
                raise ValueError(f"Agente {request.agent_type} no disponible")
            
            # Procesar la solicitud
            self.logger.info(f"Procesando solicitud con {request.agent_type.value}")
            
            result = await agent.process_request(
                request.prompt,
                context=request.parameters or {}
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Crear respuesta
            response = AgentResponse(
                success=result.get("success", True),
                content=str(result.get("content", result)),
                agent_type=request.agent_type,
                processing_time=processing_time,
                metadata=result.get("metadata", {}),
                error_message=result.get("error") if not result.get("success", True) else None
            )
            
            # Actualizar métricas
            if response.success:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1
            
            self._update_average_response_time(processing_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error procesando solicitud: {e}")
            self.metrics["failed_requests"] += 1
            
            return AgentResponse(
                success=False,
                content="",
                agent_type=request.agent_type,
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def multi_agent_collaboration(
        self, 
        task: str, 
        participating_agents: List[AgentType],
        coordination_strategy: str = "sequential"
    ) -> str:
        """
        Coordina múltiples agentes para una tarea compleja
        
        Args:
            task: Tarea compleja que requiere múltiples agentes
            participating_agents: Lista de agentes que deben participar
            coordination_strategy: Estrategia de coordinación (sequential, parallel, hierarchical)
            
        Returns:
            Resultado colaborativo
        """
        try:
            self.logger.info(f"Iniciando colaboración multi-agente: {coordination_strategy}")
            
            if self.agent_team and coordination_strategy == "team_mode":
                # Usar el equipo de Agno para coordinación avanzada
                response = await asyncio.to_thread(
                    self.agent_team.print_response,
                    task,
                    stream=False
                )
                return response
            
            # Estrategias personalizadas de coordinación
            if coordination_strategy == "sequential":
                return await self._sequential_collaboration(task, participating_agents)
            elif coordination_strategy == "parallel":
                return await self._parallel_collaboration(task, participating_agents)
            elif coordination_strategy == "hierarchical":
                return await self._hierarchical_collaboration(task, participating_agents)
            else:
                raise ValueError(f"Estrategia de coordinación no reconocida: {coordination_strategy}")
                
        except Exception as e:
            self.logger.error(f"Error en colaboración multi-agente: {e}")
            return f"Error en la colaboración: {str(e)}"
    
    async def _sequential_collaboration(
        self, 
        task: str, 
        agents: List[AgentType]
    ) -> str:
        """
        Colaboración secuencial donde cada agente construye sobre el trabajo anterior
        """
        results = []
        current_context = {"task": task}
        
        for agent_type in agents:
            agent = self.agents.get(agent_type)
            if agent:
                # Cada agente trabaja con el contexto acumulado
                result = await agent.process_request(
                    f"Contribuye a esta tarea: {task}",
                    context=current_context
                )
                
                results.append(f"=== {agent_type.value} ===\n{result.get('content', result)}")
                
                # Actualizar contexto para el siguiente agente
                current_context[f"{agent_type.value}_output"] = result
        
        return "\n\n".join(results)
    
    async def _parallel_collaboration(
        self, 
        task: str, 
        agents: List[AgentType]
    ) -> str:
        """
        Colaboración paralela donde todos los agentes trabajan simultáneamente
        """
        tasks = []
        
        for agent_type in agents:
            agent = self.agents.get(agent_type)
            if agent:
                tasks.append(
                    agent.process_request(
                        f"Contribuye a esta tarea desde tu especialidad: {task}",
                        context={"task": task, "collaboration_mode": "parallel"}
                    )
                )
        
        # Ejecutar en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combinar resultados
        combined_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                combined_results.append(f"Error en agente {agents[i].value}: {str(result)}")
            else:
                combined_results.append(f"=== {agents[i].value} ===\n{result.get('content', result)}")
        
        return "\n\n".join(combined_results)
    
    async def _hierarchical_collaboration(
        self, 
        task: str, 
        agents: List[AgentType]
    ) -> str:
        """
        Colaboración jerárquica con un agente coordinador
        """
        # El primer agente actúa como coordinador
        coordinator_type = agents[0]
        worker_agents = agents[1:]
        
        coordinator = self.agents.get(coordinator_type)
        if not coordinator:
            return "Error: Agente coordinador no disponible"
        
        # El coordinador delega tareas específicas
        coordination_prompt = f"""
        Actúa como coordinador para esta tarea: {task}
        
        Tienes disponibles estos agentes especializados: {[a.value for a in worker_agents]}
        
        Proporciona un plan de trabajo y coordina las contribuciones.
        """
        
        coordination_result = await coordinator.process_request(
            coordination_prompt,
            context={"available_agents": worker_agents, "task": task}
        )
        
        # Los otros agentes contribuyen según la coordinación
        worker_results = []
        for agent_type in worker_agents:
            agent = self.agents.get(agent_type)
            if agent:
                result = await agent.process_request(
                    f"Contribuye según la coordinación establecida: {task}",
                    context={
                        "coordination_plan": coordination_result,
                        "task": task
                    }
                )
                worker_results.append(f"=== {agent_type.value} ===\n{result.get('content', result)}")
        
        # Combinar resultados
        final_result = f"=== COORDINACIÓN ({coordinator_type.value}) ===\n{coordination_result.get('content', coordination_result)}\n\n"
        final_result += "\n\n".join(worker_results)
        
        return final_result
    
    async def search_and_answer(
        self, 
        query: str, 
        preferred_agent: Optional[AgentType] = None
    ) -> str:
        """
        Busca información en documentos y proporciona una respuesta
        
        Args:
            query: Consulta del usuario
            preferred_agent: Agente preferido para responder
            
        Returns:
            Respuesta basada en búsqueda y análisis
        """
        try:
            # Buscar documentos relevantes
            relevant_docs = await self.document_service.search_documents(query)
            
            # Seleccionar agente apropiado
            if not preferred_agent:
                preferred_agent = self._select_best_agent_for_query(query)
            
            agent = self.agents.get(preferred_agent)
            if not agent:
                preferred_agent = AgentType.TUTOR  # Fallback
                agent = self.agents.get(preferred_agent)
            
            # Construir contexto con documentos relevantes
            context = {
                "query": query,
                "relevant_documents": relevant_docs,
                "search_mode": True
            }
            
            # Procesar con el agente seleccionado
            result = await agent.process_request(
                f"Responde esta consulta basándote en los documentos disponibles: {query}",
                context=context
            )
            
            return result.get("content", str(result))
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda y respuesta: {e}")
            return f"Error procesando la consulta: {str(e)}"
    
    def _select_best_agent_for_query(self, query: str) -> AgentType:
        """
        Selecciona el mejor agente para una consulta específica
        """
        query_lower = query.lower()
        
        # Palabras clave para cada tipo de agente
        agent_keywords = {
            AgentType.EXAM_GENERATOR: ["examen", "test", "evaluación", "preguntas", "quiz"],
            AgentType.CURRICULUM_CREATOR: ["currículum", "programa", "plan de estudios", "materia"],
            AgentType.LESSON_PLANNER: ["lección", "clase", "plan de clase", "actividad"],
            AgentType.DOCUMENT_ANALYZER: ["analizar", "documento", "resumen", "contenido"],
            AgentType.TUTOR: ["explicar", "ayuda", "entender", "cómo", "por qué"]
        }
        
        # Contar coincidencias
        scores = {}
        for agent_type, keywords in agent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[agent_type] = score
        
        # Retornar el agente con mayor puntuación o tutor por defecto
        best_agent = max(scores, key=scores.get)
        return best_agent if scores[best_agent] > 0 else AgentType.TUTOR
    
    def _update_average_response_time(self, new_time: float):
        """
        Actualiza el tiempo promedio de respuesta
        """
        total_requests = self.metrics["total_requests"]
        current_avg = self.metrics["average_response_time"]
        
        # Calcular nuevo promedio
        new_avg = ((current_avg * (total_requests - 1)) + new_time) / total_requests
        self.metrics["average_response_time"] = new_avg
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de todos los agentes
        """
        status = {
            "coordinator_status": "active",
            "total_agents": len(self.agents),
            "agents": {},
            "metrics": self.metrics,
            "team_mode_available": self.agent_team is not None
        }
        
        for agent_type, agent in self.agents.items():
            status["agents"][agent_type.value] = agent.get_agent_info()
        
        return status
    
    async def shutdown(self):
        """
        Cierra el coordinador y libera recursos
        """
        self.logger.info("Cerrando coordinador de agentes...")
        
        # Aquí puedes agregar lógica de limpieza si es necesaria
        # Por ejemplo, cerrar conexiones, guardar estado, etc.
        
        self.logger.info("Coordinador cerrado exitosamente")
