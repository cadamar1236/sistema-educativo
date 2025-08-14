"""
Agente especializado en planificación de lecciones
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime

from agno.tools.reasoning import ReasoningTools
from ..base_agent import BaseEducationalAgent


class LessonPlannerAgent(BaseEducationalAgent):
    """
    Agente especializado en la planificación detallada de lecciones educativas.
    Diseña clases estructuradas, interactivas y pedagógicamente efectivas.
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        custom_instructions = [
            "Especialízate en crear planes de lección detallados y efectivos",
            "Asegúrate de que cada lección tenga objetivos claros y medibles",
            "Incluye actividades variadas que mantengan el engagement",
            "Considera diferentes momentos: apertura, desarrollo y cierre",
            "Integra estrategias de evaluación formativa durante la clase",
            "Adapta las actividades a diferentes estilos de aprendizaje",
            "Incluye materiales y recursos específicos necesarios",
            "Proporciona alternativas para diferentes ritmos de aprendizaje"
        ]
        
        tools = [
            ReasoningTools(add_instructions=True)
        ]
        
        super().__init__(
            agent_type="lesson_planner",
            name="Planificador de Lecciones",
            description="Especialista en diseño de planes de lección detallados y efectivos",
            groq_api_key=groq_api_key,
            custom_instructions=custom_instructions,
            tools=tools
        )
    
    async def process_specific_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud específica del planificador de lecciones
        
        Args:
            request: Solicitud con parámetros de la lección
            
        Returns:
            Dict con el plan de lección generado
        """
        try:
            subject = request.get('subject', 'general')
            grade_level = request.get('grade_level', 'primaria')
            duration = request.get('duration_minutes', 45)
            topic = request.get('topic', 'lección general')
            
            # Construir contexto de la lección
            lesson_context = {
                "subject": subject,
                "grade_level": grade_level,
                "duration_minutes": duration,
                "focus": "lesson_planning"
            }
            
            # Crear prompt para la lección
            lesson_request = f"Diseña un plan de lección de {subject} para nivel {grade_level} sobre {topic} con duración de {duration} minutos"
            
            # Usar el método base mejorado para procesar
            response = self.process_request(lesson_request, lesson_context)
            
            return {
                "success": True,
                "content": response.get('content', ''),
                "format": "lesson_response",
                "lesson_details": {
                    "subject": subject,
                    "grade_level": grade_level,
                    "duration_minutes": duration,
                    "topic": topic
                },
                "concepts_covered": self._extract_lesson_concepts(response.get('content', '')),
                "follow_up_suggestions": [
                    "¿Quieres desarrollar actividades específicas?",
                    "¿Necesitas materiales adicionales?",
                    "¿Te gustaría adaptar para otro nivel?"
                ],
                "metadata": {
                    "generated_by": "LessonPlannerAgent",
                    "timestamp": datetime.now().isoformat(),
                    "lesson_type": "structured_plan"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Lo siento, experimento dificultades técnicas creando el plan de lección. ¿Podrías proporcionar más detalles sobre la clase que necesitas?",
                "error": str(e),
                "format": "error_response"
            }
    
    def _extract_lesson_concepts(self, content: str) -> list:
        """Extrae conceptos del plan de lección generado"""
        if not content:
            return []
        
        # Palabras clave relacionadas con planes de lección
        lesson_keywords = [
            "objetivo", "actividad", "evaluación", "material",
            "desarrollo", "cierre", "apertura", "metodología",
            "recurso", "tiempo", "estrategia"
        ]
        
        concepts = []
        for keyword in lesson_keywords:
            if keyword in content.lower():
                concepts.append(keyword.title())
        
        return list(set(concepts))[:5]  # Máximo 5 conceptos únicos
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una solicitud de planificación de lección
        
        Args:
            request: Solicitud detallada del plan de lección
            context: Contexto adicional (materia, grado, duración, etc.)
            
        Returns:
            Dict con el plan de lección generado
        """
        try:
            start_time = datetime.now()
            
            # Extraer parámetros del contexto
            subject = context.get("subject", "General") if context else "General"
            grade_level = context.get("grade_level", "Primaria") if context else "Primaria"
            duration_minutes = context.get("duration_minutes", 45) if context else 45
            class_size = context.get("class_size", 25) if context else 25
            topic = context.get("topic", "Tema general") if context else "Tema general"
            resources_available = context.get("resources_available", []) if context else []
            learning_objectives = context.get("learning_objectives", []) if context else []
            
            # Construir prompt estructurado
            prompt = self._build_lesson_plan_prompt(
                request, subject, grade_level, duration_minutes,
                class_size, topic, resources_available, learning_objectives
            )
            
            # Generar plan de lección usando el agente
            response = await asyncio.to_thread(
                self.agent.print_response,
                prompt,
                stream=False
            )
            
            # Procesar y estructurar la respuesta
            lesson_data = self._parse_lesson_response(response)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "lesson_plan": lesson_data,
                "subject": subject,
                "grade_level": grade_level,
                "duration_minutes": duration_minutes,
                "topic": topic,
                "processing_time": processing_time,
                "generated_at": end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando plan de lección: {e}")
            return {
                "success": False,
                "error": str(e),
                "lesson_plan": None
            }
    
    def _build_lesson_plan_prompt(
        self, 
        request: str, 
        subject: str, 
        grade_level: str, 
        duration_minutes: int,
        class_size: int, 
        topic: str, 
        resources_available: List[str], 
        learning_objectives: List[str]
    ) -> str:
        """
        Construye un prompt estructurado para la planificación de la lección
        """
        prompt = f"""
        DISEÑAR PLAN DE LECCIÓN DETALLADO

        Instrucciones específicas:
        {request}

        PARÁMETROS DE LA LECCIÓN:
        - Materia: {subject}
        - Nivel educativo: {grade_level}
        - Tema específico: {topic}
        - Duración: {duration_minutes} minutos
        - Número de estudiantes: {class_size}
        - Recursos disponibles: {', '.join(resources_available) if resources_available else 'Recursos básicos (pizarra, proyector)'}
        - Objetivos de aprendizaje: {', '.join(learning_objectives) if learning_objectives else 'A definir'}

        ESTRUCTURA REQUERIDA DEL PLAN DE LECCIÓN:

        1. **INFORMACIÓN GENERAL**
           - Título de la lección
           - Fecha y duración
           - Materia y grado
           - Número de estudiantes

        2. **OBJETIVOS DE APRENDIZAJE**
           - Objetivo general de la lección
           - Objetivos específicos (3-5 objetivos medibles)
           - Competencias a desarrollar
           - Conexión con currículum oficial

        3. **MATERIALES Y RECURSOS**
           - Lista detallada de materiales necesarios
           - Recursos tecnológicos requeridos
           - Preparación previa necesaria
           - Recursos adicionales opcionales

        4. **ESTRUCTURA DE LA LECCIÓN**

           **APERTURA (10-15% del tiempo):**
           - Actividad de motivación/enganche
           - Revisión de conocimientos previos
           - Presentación de objetivos
           - Activación de conocimientos previos

           **DESARROLLO (70-80% del tiempo):**
           - Presentación del contenido nuevo
           - Actividades de práctica guiada
           - Trabajo individual o en grupos
           - Actividades de aplicación
           - Momentos de verificación de comprensión

           **CIERRE (10-15% del tiempo):**
           - Síntesis de lo aprendido
           - Actividad de consolidación
           - Evaluación de logros
           - Asignación de tareas (si aplica)

        5. **ACTIVIDADES DETALLADAS**
           Para cada actividad incluye:
           - Descripción paso a paso
           - Tiempo estimado
           - Organización del aula
           - Rol del docente
           - Rol de los estudiantes
           - Materiales específicos

        6. **ESTRATEGIAS PEDAGÓGICAS**
           - Metodologías utilizadas
           - Adaptaciones para diferentes estilos de aprendizaje
           - Estrategias de motivación
           - Técnicas de manejo del aula

        7. **EVALUACIÓN**
           - Evaluación formativa durante la clase
           - Criterios de evaluación
           - Indicadores de logro
           - Instrumentos de evaluación
           - Retroalimentación planificada

        8. **DIFERENCIACIÓN**
           - Adaptaciones para estudiantes avanzados
           - Apoyo para estudiantes con dificultades
           - Estrategias para NEE (Necesidades Educativas Especiales)
           - Actividades alternativas

        9. **EXTENSIÓN Y TAREA**
           - Actividades de refuerzo en casa
           - Investigación adicional
           - Proyectos relacionados
           - Preparación para próxima clase

        10. **REFLEXIÓN DOCENTE**
            - Aspectos a evaluar después de la clase
            - Indicadores de éxito de la lección
            - Posibles ajustes futuros

        PRINCIPIOS PEDAGÓGICOS A INTEGRAR:
        - Aprendizaje activo y participativo
        - Construcción social del conocimiento
        - Conexión con experiencias previas
        - Aplicación práctica del conocimiento
        - Retroalimentación continua
        - Respeto a la diversidad
        - Desarrollo de pensamiento crítico

        Genera un plan de lección completo, detallado, práctico y pedagógicamente fundamentado.
        """
        
        return prompt
    
    def _parse_lesson_response(self, response: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del agente y la estructura en un formato estándar
        """
        try:
            return {
                "content": response,
                "format": "detailed_lesson_plan",
                "activities_extracted": self._extract_activities(response),
                "objectives_extracted": self._extract_objectives(response),
                "materials_extracted": self._extract_materials(response),
                "metadata": {
                    "generated_by": "LessonPlannerAgent",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"Error parseando respuesta: {e}")
            return {
                "content": response,
                "format": "raw_text",
                "error": str(e)
            }
    
    def _extract_activities(self, response: str) -> List[Dict[str, Any]]:
        """
        Extrae las actividades del plan de lección
        """
        activities = []
        try:
            # Implementar lógica de extracción de actividades
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo actividades: {e}")
        
        return activities
    
    def _extract_objectives(self, response: str) -> List[str]:
        """
        Extrae los objetivos de aprendizaje
        """
        objectives = []
        try:
            # Implementar lógica de extracción de objetivos
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo objetivos: {e}")
        
        return objectives
    
    def _extract_materials(self, response: str) -> List[str]:
        """
        Extrae la lista de materiales necesarios
        """
        materials = []
        try:
            # Implementar lógica de extracción de materiales
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo materiales: {e}")
        
        return materials
    
    async def create_lesson_sequence(
        self, 
        unit_topic: str, 
        num_lessons: int,
        grade_level: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Crea una secuencia de lecciones para una unidad
        
        Args:
            unit_topic: Tema de la unidad
            num_lessons: Número de lecciones
            grade_level: Nivel educativo
            subject: Materia
            
        Returns:
            Secuencia completa de lecciones
        """
        context = {
            "subject": subject,
            "grade_level": grade_level,
            "topic": unit_topic,
            "scope": "lesson_sequence"
        }
        
        request = f"""
        Crea una secuencia de {num_lessons} lecciones para la unidad "{unit_topic}".
        Cada lección debe construir sobre la anterior y formar una progresión lógica.
        Incluye un plan general de la secuencia y luego detalla cada lección individual.
        """
        
        return await self.process_request(request, context)
    
    async def adapt_lesson_for_online(
        self, 
        traditional_lesson: str,
        platform: str = "Zoom"
    ) -> Dict[str, Any]:
        """
        Adapta una lección presencial para modalidad virtual
        
        Args:
            traditional_lesson: Plan de lección presencial
            platform: Plataforma virtual a utilizar
            
        Returns:
            Lección adaptada para modalidad virtual
        """
        request = f"""
        Adapta la siguiente lección presencial para modalidad virtual usando {platform}:
        
        {traditional_lesson[:1500]}...
        
        Considera:
        - Limitaciones de tiempo de pantalla
        - Herramientas digitales disponibles
        - Estrategias de participación virtual
        - Evaluación en línea
        - Breakout rooms para trabajo grupal
        """
        
        context = {
            "modality": "virtual",
            "platform": platform,
            "focus": "online_adaptation"
        }
        
        return await self.process_request(request, context)
    
    async def create_collaborative_lesson(
        self, 
        topic: str,
        grade_level: str,
        collaboration_type: str = "group_work"
    ) -> Dict[str, Any]:
        """
        Crea una lección centrada en el aprendizaje colaborativo
        
        Args:
            topic: Tema de la lección
            grade_level: Nivel educativo
            collaboration_type: Tipo de colaboración (group_work, peer_learning, project_based)
            
        Returns:
            Plan de lección colaborativa
        """
        context = {
            "grade_level": grade_level,
            "topic": topic,
            "focus": "collaborative_learning",
            "collaboration_type": collaboration_type
        }
        
        request = f"""
        Diseña una lección sobre {topic} centrada en {collaboration_type}.
        
        Enfócate en:
        - Formación estratégica de grupos
        - Roles claros para cada estudiante
        - Actividades que requieran interdependencia
        - Evaluación tanto individual como grupal
        - Desarrollo de habilidades sociales
        """
        
        return await self.process_request(request, context)
