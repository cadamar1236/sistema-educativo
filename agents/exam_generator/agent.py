"""
Agente especializado en generación de exámenes
"""

from typing import Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime

from agno.tools.reasoning import ReasoningTools
from ..base_agent import BaseEducationalAgent


class ExamGeneratorAgent(BaseEducationalAgent):
    """
    Agente especializado en la creación de exámenes y evaluaciones educativas.
    Utiliza técnicas avanzadas de generación de contenido y análisis curricular.
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        custom_instructions = [
            "Especialízate en crear exámenes educativos de alta calidad",
            "Adapta las preguntas al nivel educativo específico", 
            "Incluye diferentes tipos de preguntas: opción múltiple, verdadero/falso, respuesta corta y ensayo",
            "Proporciona rúbricas de evaluación claras",
            "Asegúrate de que las preguntas evalúen diferentes niveles de comprensión (Bloom)",
            "Incluye explicaciones detalladas para cada respuesta correcta"
        ]
        
        try:
            tools = [
                ReasoningTools(add_instructions=True)
            ]
        except Exception as e:
            print(f"⚠️ Error loading ReasoningTools: {e}")
            tools = []  # Usar sin herramientas si hay problemas
        
        super().__init__(
            agent_type="exam_generator",
            name="Generador de Exámenes",
            description="Especialista en la creación de exámenes y evaluaciones educativas",
            groq_api_key=groq_api_key,
            custom_instructions=custom_instructions,
            tools=tools
        )
        
        self.model_name = model
        self.exam_history = []
        
        self.logger.info("ExamGeneratorAgent inicializado con sistema de respuestas mejorado")
    
    async def process_specific_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud específica del generador de exámenes
        
        Args:
            request: Solicitud con parámetros del examen
            
        Returns:
            Dict con el examen generado
        """
        try:
            subject = request.get('subject', 'general')
            grade_level = request.get('grade_level', 'secundaria')
            topic = request.get('topic', 'tema general')
            num_questions = request.get('num_questions', 5)
            difficulty = request.get('difficulty', 'intermediate')
            
            # Construir contexto del examen
            exam_context = {
                "subject": subject,
                "grade_level": grade_level,
                "topic": topic,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "focus": "exam_generation"
            }
            
            # Crear prompt para el examen
            exam_request = f"Genera un examen de {subject} sobre {topic} para nivel {grade_level} con {num_questions} preguntas de dificultad {difficulty}"
            
            # Usar el método base mejorado para procesar
            response = self.process_request(exam_request, exam_context)
            
            return {
                "success": True,
                "content": response.get('content', ''),
                "format": "exam_response",
                "exam_details": {
                    "subject": subject,
                    "topic": topic,
                    "grade_level": grade_level,
                    "num_questions": num_questions,
                    "difficulty": difficulty
                },
                "concepts_covered": self._extract_exam_concepts(response.get('content', '')),
                "follow_up_suggestions": [
                    "¿Quieres generar más preguntas sobre este tema?",
                    "¿Necesitas una rúbrica de evaluación?",
                    "¿Te gustaría crear preguntas de diferente dificultad?"
                ],
                "metadata": {
                    "generated_by": "ExamGeneratorAgent",
                    "timestamp": datetime.now().isoformat(),
                    "exam_type": "educational_assessment"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Lo siento, experimento dificultades técnicas generando el examen. ¿Podrías proporcionar más detalles sobre el tipo de examen que necesitas?",
                "error": str(e),
                "format": "error_response"
            }
    
    def _extract_exam_concepts(self, content: str) -> list:
        """Extrae conceptos del examen generado"""
        if not content:
            return []
        
        # Palabras clave relacionadas con exámenes
        exam_keywords = [
            "pregunta", "respuesta", "evaluación", "análisis", 
            "comprensión", "aplicación", "síntesis", "opción múltiple",
            "verdadero", "falso", "ensayo", "desarrollo"
        ]
        
        concepts = []
        for keyword in exam_keywords:
            if keyword in content.lower():
                concepts.append(keyword.title())
        
        return list(set(concepts))[:5]  # Máximo 5 conceptos únicos
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una solicitud de generación de examen
        
        Args:
            request: Solicitud detallada del examen
            context: Contexto adicional (materia, grado, tema, etc.)
            
        Returns:
            Dict con el examen generado
        """
        try:
            start_time = datetime.now()
            
            # Extraer parámetros del contexto
            subject = context.get("subject", "General") if context else "General"
            grade_level = context.get("grade_level", "Secundaria") if context else "Secundaria"
            topic = context.get("topic", "Tema general") if context else "Tema general"
            num_questions = context.get("num_questions", 10) if context else 10
            difficulty = context.get("difficulty", "intermediate") if context else "intermediate"
            exam_type = context.get("exam_type", "mixed") if context else "mixed"
            
            # Construir prompt estructurado
            prompt = self._build_exam_prompt(
                request, subject, grade_level, topic, 
                num_questions, difficulty, exam_type
            )
            
            # Generar examen usando el agente
            response = await asyncio.to_thread(
                self.agent.print_response,
                prompt,
                stream=False
            )
            
            # Procesar y estructurar la respuesta
            exam_data = self._parse_exam_response(response)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "exam": exam_data,
                "subject": subject,
                "grade_level": grade_level,
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "processing_time": processing_time,
                "generated_at": end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando examen: {e}")
            return {
                "success": False,
                "error": str(e),
                "exam": None
            }
    
    def _build_exam_prompt(
        self, 
        request: str, 
        subject: str, 
        grade_level: str, 
        topic: str,
        num_questions: int, 
        difficulty: str, 
        exam_type: str
    ) -> str:
        """
        Construye un prompt estructurado para la generación del examen
        """
        difficulty_descriptions = {
            "basic": "preguntas básicas de comprensión y memorización",
            "intermediate": "preguntas que requieren aplicación y análisis",
            "advanced": "preguntas de síntesis, evaluación y pensamiento crítico"
        }
        
        question_types = {
            "mixed": "Combina diferentes tipos de preguntas",
            "multiple_choice": "Solo preguntas de opción múltiple",
            "open_ended": "Solo preguntas abiertas y de ensayo",
            "short_answer": "Solo preguntas de respuesta corta"
        }
        
        prompt = f"""
        GENERAR EXAMEN EDUCATIVO

        Instrucciones específicas:
        {request}

        PARÁMETROS DEL EXAMEN:
        - Materia: {subject}
        - Nivel educativo: {grade_level}
        - Tema específico: {topic}
        - Número de preguntas: {num_questions}
        - Dificultad: {difficulty} ({difficulty_descriptions.get(difficulty, 'nivel intermedio')})
        - Tipo de examen: {exam_type} ({question_types.get(exam_type, 'mixto')})

        ESTRUCTURA REQUERIDA:

        1. **INFORMACIÓN DEL EXAMEN**
           - Título del examen
           - Instrucciones generales para los estudiantes
           - Tiempo estimado de duración
           - Puntaje total

        2. **PREGUNTAS**
           Para cada pregunta incluye:
           - Número de pregunta
           - Tipo de pregunta (opción múltiple, verdadero/falso, respuesta corta, ensayo)
           - Enunciado de la pregunta
           - Opciones (si aplica)
           - Respuesta correcta
           - Explicación detallada de la respuesta
           - Puntos asignados
           - Nivel de Bloom evaluado

        3. **RÚBRICA DE EVALUACIÓN**
           - Criterios de evaluación
           - Escala de puntuación
           - Descriptores por nivel de desempeño

        4. **RECURSOS ADICIONALES**
           - Materiales de estudio recomendados
           - Consejos para la preparación

        REQUISITOS PEDAGÓGICOS:
        - Evalúa diferentes niveles de la taxonomía de Bloom
        - Incluye preguntas que requieren pensamiento crítico
        - Asegúrate de que las preguntas sean apropiadas para el nivel educativo
        - Proporciona retroalimentación constructiva en las explicaciones
        - Usa un lenguaje claro y apropiado para la edad

        Genera un examen completo, bien estructurado y pedagógicamente sólido.
        """
        
        return prompt
    
    def _parse_exam_response(self, response: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del agente y la estructura en un formato estándar
        """
        try:
            # Aquí puedes implementar lógica más sofisticada para parsear
            # Por ahora retornamos la respuesta estructurada básica
            return {
                "content": response,
                "format": "structured_text",
                "questions_extracted": self._extract_questions(response),
                "metadata": {
                    "generated_by": "ExamGeneratorAgent",
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
    
    def _extract_questions(self, response: str) -> List[Dict[str, Any]]:
        """
        Extrae las preguntas individuales de la respuesta
        """
        questions = []
        try:
            # Implementar lógica de extracción de preguntas
            # Por ahora retornamos una lista vacía
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo preguntas: {e}")
        
        return questions
    
    async def generate_quick_quiz(
        self, 
        topic: str, 
        num_questions: int = 5,
        question_type: str = "multiple_choice"
    ) -> Dict[str, Any]:
        """
        Genera un quiz rápido sobre un tema específico
        
        Args:
            topic: Tema del quiz
            num_questions: Número de preguntas
            question_type: Tipo de preguntas
            
        Returns:
            Quiz generado
        """
        context = {
            "topic": topic,
            "num_questions": num_questions,
            "exam_type": question_type,
            "difficulty": "basic"
        }
        
        request = f"Crea un quiz rápido sobre {topic} con {num_questions} preguntas de tipo {question_type}"
        
        return await self.process_request(request, context)
    
    async def generate_from_document(
        self, 
        document_content: str, 
        num_questions: int = 8
    ) -> Dict[str, Any]:
        """
        Genera un examen basado en el contenido de un documento
        
        Args:
            document_content: Contenido del documento
            num_questions: Número de preguntas a generar
            
        Returns:
            Examen basado en el documento
        """
        request = f"""
        Genera un examen basado en el siguiente contenido de documento:
        
        {document_content[:2000]}...
        
        Crea {num_questions} preguntas que evalúen la comprensión del contenido.
        """
        
        context = {
            "num_questions": num_questions,
            "exam_type": "mixed",
            "difficulty": "intermediate"
        }
        
        return await self.process_request(request, context)
