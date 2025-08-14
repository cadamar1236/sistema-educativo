"""
Agente especializado en creación de currículums educativos
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime

from agno.tools.reasoning import ReasoningTools
from ..base_agent import BaseEducationalAgent


class CurriculumCreatorAgent(BaseEducationalAgent):
    """
    Agente especializado en la creación de currículums y planes de estudio.
    Diseña programas educativos completos, estructurados y progresivos.
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        custom_instructions = [
            "Especialízate en diseñar currículums educativos comprehensivos",
            "Asegúrate de que el contenido sea progresivo y apropiado para la edad",
            "Incluye objetivos de aprendizaje claros y medibles",
            "Proporciona actividades diversas e interactivas",
            "Considera diferentes estilos de aprendizaje",
            "Integra evaluaciones formativas y sumativas",
            "Alinea el currículum con estándares educativos nacionales e internacionales"
        ]
        
        tools = [
            ReasoningTools(add_instructions=True)
        ]
        
        super().__init__(
            agent_type="curriculum_creator",
            name="Creador de Currículum",
            description="Especialista en diseño de currículums y programas educativos",
            groq_api_key=groq_api_key,
            custom_instructions=custom_instructions,
            tools=tools
        )
    
    async def process_specific_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud específica del creador de currículum
        
        Args:
            request: Solicitud con parámetros del currículum
            
        Returns:
            Dict con el currículum generado
        """
        try:
            subject = request.get('subject', 'general')
            grade_level = request.get('grade_level', 'primaria')
            duration = request.get('duration_weeks', 12)
            topic = request.get('topic', 'currículum general')
            
            # Construir contexto del currículum
            curriculum_context = {
                "subject": subject,
                "grade_level": grade_level,
                "duration_weeks": duration,
                "focus": "curriculum_creation"
            }
            
            # Crear prompt para el currículum
            curriculum_request = f"Diseña un currículum de {subject} para nivel {grade_level} con duración de {duration} semanas sobre {topic}"
            
            # Usar el método base mejorado para procesar
            response = self.process_request(curriculum_request, curriculum_context)
            
            return {
                "success": True,
                "content": response.get('content', ''),
                "format": "curriculum_response",
                "curriculum_details": {
                    "subject": subject,
                    "grade_level": grade_level,
                    "duration_weeks": duration,
                    "topic": topic
                },
                "concepts_covered": self._extract_curriculum_concepts(response.get('content', '')),
                "follow_up_suggestions": [
                    "¿Quieres desarrollar unidades específicas?",
                    "¿Necesitas actividades de evaluación?",
                    "¿Te gustaría adaptar para otro nivel?"
                ],
                "metadata": {
                    "generated_by": "CurriculumCreatorAgent",
                    "timestamp": datetime.now().isoformat(),
                    "curriculum_type": "educational_program"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Lo siento, experimento dificultades técnicas creando el currículum. ¿Podrías proporcionar más detalles sobre el programa que necesitas?",
                "error": str(e),
                "format": "error_response"
            }
    
    def _extract_curriculum_concepts(self, content: str) -> list:
        """Extrae conceptos del currículum generado"""
        if not content:
            return []
        
        # Palabras clave relacionadas con currículum
        curriculum_keywords = [
            "objetivo", "competencia", "habilidad", "conocimiento",
            "unidad", "módulo", "evaluación", "actividad",
            "metodología", "recurso", "estándar"
        ]
        
        concepts = []
        for keyword in curriculum_keywords:
            if keyword in content.lower():
                concepts.append(keyword.title())
        
        return list(set(concepts))[:5]  # Máximo 5 conceptos únicos
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una solicitud de creación de currículum
        
        Args:
            request: Solicitud detallada del currículum
            context: Contexto adicional (materia, grado, duración, etc.)
            
        Returns:
            Dict con el currículum generado
        """
        try:
            start_time = datetime.now()
            
            # Extraer parámetros del contexto
            subject = context.get("subject", "General") if context else "General"
            grade_level = context.get("grade_level", "Primaria") if context else "Primaria"
            duration_weeks = context.get("duration_weeks", 12) if context else 12
            language = context.get("language", "Español") if context else "Español"
            education_system = context.get("education_system", "Nacional") if context else "Nacional"
            
            # Construir prompt estructurado
            prompt = self._build_curriculum_prompt(
                request, subject, grade_level, duration_weeks, 
                language, education_system
            )
            
            # Generar currículum usando el agente
            response = await asyncio.to_thread(
                self.agent.print_response,
                prompt,
                stream=False
            )
            
            # Procesar y estructurar la respuesta
            curriculum_data = self._parse_curriculum_response(response)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "curriculum": curriculum_data,
                "subject": subject,
                "grade_level": grade_level,
                "duration_weeks": duration_weeks,
                "language": language,
                "processing_time": processing_time,
                "generated_at": end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando currículum: {e}")
            return {
                "success": False,
                "error": str(e),
                "curriculum": None
            }
    
    def _build_curriculum_prompt(
        self, 
        request: str, 
        subject: str, 
        grade_level: str, 
        duration_weeks: int,
        language: str, 
        education_system: str
    ) -> str:
        """
        Construye un prompt estructurado para la generación del currículum
        """
        prompt = f"""
        DISEÑAR CURRÍCULUM EDUCATIVO COMPLETO

        Instrucciones específicas:
        {request}

        PARÁMETROS DEL CURRÍCULUM:
        - Materia: {subject}
        - Nivel educativo: {grade_level}
        - Duración: {duration_weeks} semanas
        - Idioma de instrucción: {language}
        - Sistema educativo: {education_system}

        ESTRUCTURA REQUERIDA DEL CURRÍCULUM:

        1. **INFORMACIÓN GENERAL**
           - Título del programa
           - Descripción general
           - Población objetivo
           - Prerrequisitos
           - Duración total y carga horaria

        2. **OBJETIVOS EDUCATIVOS**
           - Objetivo general del programa
           - Objetivos específicos por unidad
           - Competencias a desarrollar
           - Habilidades del siglo XXI

        3. **ESTRUCTURA CURRICULAR**
           Para cada semana/unidad incluye:
           - Número de unidad/semana
           - Título de la unidad
           - Objetivos de aprendizaje específicos
           - Contenidos conceptuales, procedimentales y actitudinales
           - Actividades de aprendizaje
           - Recursos necesarios
           - Tiempo estimado
           - Evaluación formativa y sumativa

        4. **METODOLOGÍA PEDAGÓGICA**
           - Enfoques pedagógicos utilizados
           - Estrategias de enseñanza
           - Adaptaciones para diferentes estilos de aprendizaje
           - Uso de tecnología educativa

        5. **EVALUACIÓN**
           - Criterios de evaluación
           - Instrumentos de evaluación
           - Rúbricas de calificación
           - Evaluación formativa continua
           - Evaluación sumativa

        6. **RECURSOS Y MATERIALES**
           - Materiales didácticos requeridos
           - Recursos tecnológicos
           - Bibliografia y fuentes
           - Espacios físicos necesarios

        7. **CRONOGRAMA DETALLADO**
           - Planificación semanal
           - Distribución de contenidos
           - Fechas de evaluaciones
           - Actividades especiales

        8. **ADAPTACIONES CURRICULARES**
           - Estrategias para estudiantes con NEE
           - Actividades de refuerzo
           - Actividades de enriquecimiento
           - Apoyo diferenciado

        PRINCIPIOS PEDAGÓGICOS A CONSIDERAR:
        - Aprendizaje significativo y constructivista
        - Desarrollo de pensamiento crítico
        - Aprendizaje colaborativo
        - Conexión con la vida real
        - Evaluación auténtica
        - Inclusión y diversidad
        - Sostenibilidad y ciudadanía global

        Genera un currículum completo, coherente, progresivo y pedagógicamente fundamentado.
        """
        
        return prompt
    
    def _parse_curriculum_response(self, response: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del agente y la estructura en un formato estándar
        """
        try:
            return {
                "content": response,
                "format": "structured_curriculum",
                "units_extracted": self._extract_units(response),
                "objectives_extracted": self._extract_objectives(response),
                "metadata": {
                    "generated_by": "CurriculumCreatorAgent",
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
    
    def _extract_units(self, response: str) -> List[Dict[str, Any]]:
        """
        Extrae las unidades del currículum
        """
        units = []
        try:
            # Implementar lógica de extracción de unidades
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo unidades: {e}")
        
        return units
    
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
    
    async def create_unit_plan(
        self, 
        unit_topic: str, 
        grade_level: str,
        duration_days: int = 5
    ) -> Dict[str, Any]:
        """
        Crea un plan detallado para una unidad específica
        
        Args:
            unit_topic: Tema de la unidad
            grade_level: Nivel educativo
            duration_days: Duración en días
            
        Returns:
            Plan de unidad detallado
        """
        context = {
            "grade_level": grade_level,
            "duration_weeks": 1,
            "focus": "unit_planning"
        }
        
        request = f"""
        Crea un plan detallado para una unidad educativa sobre {unit_topic}.
        La unidad debe durar {duration_days} días de clase.
        Incluye actividades diarias, objetivos específicos y evaluaciones.
        """
        
        return await self.process_request(request, context)
    
    async def adapt_curriculum_for_needs(
        self, 
        base_curriculum: str, 
        special_needs: List[str]
    ) -> Dict[str, Any]:
        """
        Adapta un currículum existente para necesidades educativas especiales
        
        Args:
            base_curriculum: Currículum base
            special_needs: Lista de necesidades especiales a considerar
            
        Returns:
            Currículum adaptado
        """
        request = f"""
        Adapta el siguiente currículum para atender las siguientes necesidades educativas especiales:
        {', '.join(special_needs)}
        
        Currículum base:
        {base_curriculum[:1500]}...
        
        Proporciona adaptaciones específicas, estrategias diferenciadas y recursos especializados.
        """
        
        context = {
            "focus": "curriculum_adaptation",
            "special_needs": special_needs
        }
        
        return await self.process_request(request, context)
    
    async def generate_yearly_plan(
        self, 
        subject: str, 
        grade_level: str,
        academic_calendar: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Genera un plan curricular anual completo
        
        Args:
            subject: Materia
            grade_level: Nivel educativo
            academic_calendar: Calendario académico opcional
            
        Returns:
            Plan curricular anual
        """
        weeks_per_year = 36 if not academic_calendar else academic_calendar.get("weeks", 36)
        
        context = {
            "subject": subject,
            "grade_level": grade_level,
            "duration_weeks": weeks_per_year,
            "scope": "yearly_plan"
        }
        
        request = f"""
        Diseña un plan curricular anual completo para {subject} en {grade_level}.
        El año académico tiene {weeks_per_year} semanas.
        
        Incluye:
        - Distribución por trimestres/semestres
        - Secuenciación lógica de contenidos
        - Integración interdisciplinaria
        - Proyectos especiales
        - Evaluaciones periódicas
        """
        
        return await self.process_request(request, context)
