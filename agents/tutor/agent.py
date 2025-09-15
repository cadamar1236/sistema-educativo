"""
Agente tutor personalizado para estudiantes
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime

from agno.tools.reasoning import ReasoningTools
from ..base_agent import BaseEducationalAgent


class TutorAgent(BaseEducationalAgent):
    """
    Agente tutor personalizado que proporciona apoyo educativo individualizado.
    Adapta su enseñanza al estilo de aprendizaje y necesidades del estudiante.
    """
    
    def __init__(self, groq_api_key: str, model: str = "openai/gpt-oss-20b"):
        """
        Inicializa el Tutor Agent con el sistema mejorado de captura de respuestas
        """
        custom_instructions = [
            "Eres un tutor paciente y comprensivo",
            "Adapta tu explicación al nivel y estilo de aprendizaje del estudiante",
            "Usa ejemplos concretos y analogías apropiadas para la edad",
            "Fomenta la confianza y motivación del estudiante",
            "Identifica las dificultades específicas y proporciona apoyo dirigido",
            "Celebra los logros y proporciona retroalimentación constructiva",
            "Utiliza preguntas guía para promover el descubrimiento",
            "Conecta los conceptos con experiencias de la vida real",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
        
        try:
            tools = [
                ReasoningTools(add_instructions=True)
            ]
        except Exception as e:
            print(f"⚠️ Error loading ReasoningTools: {e}")
            tools = []  # Usar sin herramientas si hay problemas
        
        super().__init__(
            agent_type="tutor",
            name="Tutor Personal",
            description="Tutor personalizado especializado en apoyo educativo individualizado",
            groq_api_key=groq_api_key,
            custom_instructions=custom_instructions,
            tools=tools
        )
        
        self.model_name = model
        self.tutoring_sessions = []
        self.student_progress = {}
        
        self.logger.info("TutorAgent inicializado con sistema de respuestas mejorado")
    
    async def process_specific_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud específica del tutor
        
        Args:
            request: Solicitud con información del estudiante y pregunta
            
        Returns:
            Dict con la respuesta tutorial personalizada
        """
        try:
            student_level = request.get('level', 'general')
            subject = request.get('subject', 'general')
            question = request.get('question', '')
            learning_style = request.get('learning_style', 'visual')
            
            # Construir contexto tutorial personalizado
            tutorial_context = {
                "student_level": student_level,
                "subject": subject,
                "learning_style": learning_style,
                "focus": "tutoring"
            }
            
            # Usar el método get_response directamente para evitar problemas async/sync
            prompt = f"""
            Como tutor especializado, ayuda a un estudiante de {student_level} con esta pregunta sobre {subject}:
            
            Pregunta: {question}
            Estilo de aprendizaje preferido: {learning_style}
            
            Proporciona una explicación tutorial clara, didáctica y apropiada para el nivel del estudiante.
            Incluye ejemplos y pasos específicos cuando sea necesario.
            """
            
            response_content = self.get_response(prompt)
            
            return {
                "success": True,
                "content": response_content,
                "format": "tutorial_response",
                "concepts_covered": self._extract_concepts(response_content),
                "follow_up_suggestions": [
                    "¿Te gustaría que profundice en algún concepto?",
                    "¿Quieres ver más ejemplos?",
                    "¿Necesitas ayuda con ejercicios prácticos?"
                ],
                "metadata": {
                    "generated_by": "TutorAgent",
                    "timestamp": datetime.now().isoformat(),
                    "subject": subject,
                    "level": student_level
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Lo siento, experimento dificultades técnicas. Como tu tutor, te sugiero que reformulemos tu pregunta. ¿En qué tema específico necesitas ayuda?",
                "error": str(e),
                "format": "error_response"
            }
    
    def _extract_concepts(self, content: str) -> list:
        """Extrae conceptos básicos del contenido"""
        if not content:
            return []
        
        # Palabras clave educativas comunes
        educational_keywords = [
            "concepto", "teoría", "principio", "método", "fórmula",
            "proceso", "análisis", "ejemplo", "práctica", "ejercicio"
        ]
        
        concepts = []
        words = content.lower().split()
        
        for keyword in educational_keywords:
            if keyword in content.lower():
                concepts.append(keyword.title())
        
        return list(set(concepts))[:3]  # Máximo 3 conceptos únicos
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una solicitud de tutoría personalizada
        
        Args:
            request: Pregunta o tema que necesita el estudiante
            context: Contexto del estudiante (perfil, dificultades, etc.)
            
        Returns:
            Dict con la respuesta tutorial personalizada
        """
        try:
            start_time = datetime.now()
            
            # Extraer información del estudiante del contexto
            student_grade = context.get("student_grade", "Primaria") if context else "Primaria"
            learning_style = context.get("learning_style", "Visual") if context else "Visual"
            difficulty_areas = context.get("difficulty_areas", []) if context else []
            interests = context.get("interests", []) if context else []
            previous_knowledge = context.get("previous_knowledge", "") if context else ""
            
            # Construir prompt personalizado
            prompt = self._build_tutoring_prompt(
                request, student_grade, learning_style, 
                difficulty_areas, interests, previous_knowledge
            )
            
            # Generar respuesta tutorial usando el agente
            response = await asyncio.to_thread(
                self.agent.print_response,
                prompt,
                stream=False
            )
            
            # Procesar la respuesta
            tutoring_data = self._parse_tutoring_response(response)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "tutorial_response": tutoring_data,
                "student_profile": {
                    "grade": student_grade,
                    "learning_style": learning_style,
                    "difficulty_areas": difficulty_areas,
                    "interests": interests
                },
                "processing_time": processing_time,
                "generated_at": end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error en tutoría: {e}")
            # Devolver una respuesta de error amigable
            return {
                "success": False,
                "error": str(e),
                "tutorial_response": f"Lo siento, tuve un problema técnico procesando tu pregunta sobre '{request}'. Sin embargo, puedo ayudarte de forma básica: si tienes dudas sobre este tema, te recomiendo revisar los conceptos fundamentales y practicar con ejemplos simples. ¿Podrías reformular tu pregunta de manera más específica?"
            }
    
    def _build_tutoring_prompt(
        self, 
        request: str, 
        student_grade: str, 
        learning_style: str,
        difficulty_areas: List[str], 
        interests: List[str], 
        previous_knowledge: str
    ) -> str:
        """
        Construye un prompt personalizado para la tutoría
        """
        learning_style_strategies = {
            "Visual": "usa diagramas, gráficos, colores y representaciones visuales",
            "Auditivo": "explica verbalmente, usa ritmos, canciones y repetición oral",
            "Kinestésico": "incluye actividades prácticas, movimiento y manipulación de objetos",
            "Lector/Escritor": "proporciona textos, listas, notas escritas y actividades de escritura"
        }
        
        prompt = f"""
        SESIÓN DE TUTORÍA PERSONALIZADA

        PREGUNTA/TEMA DEL ESTUDIANTE:
        {request}

        PERFIL DEL ESTUDIANTE:
        - Nivel educativo: {student_grade}
        - Estilo de aprendizaje principal: {learning_style}
        - Estrategia recomendada: {learning_style_strategies.get(learning_style, "combina diferentes enfoques")}
        - Áreas de dificultad conocidas: {', '.join(difficulty_areas) if difficulty_areas else 'Ninguna identificada'}
        - Intereses del estudiante: {', '.join(interests) if interests else 'No especificados'}
        - Conocimiento previo: {previous_knowledge if previous_knowledge else 'No especificado'}

        INSTRUCCIONES PARA LA TUTORÍA:

        1. **DIAGNÓSTICO INICIAL**
           - Evalúa qué entiende el estudiante del tema
           - Identifica conceptos erróneos o confusiones
           - Determina el punto de partida apropiado

        2. **EXPLICACIÓN PERSONALIZADA**
           - Usa el estilo de aprendizaje preferido del estudiante
           - Incorpora sus intereses para hacer conexiones
           - Explica paso a paso con ejemplos concretos
           - Utiliza analogías apropiadas para su edad

        3. **PRÁCTICA GUIADA**
           - Proporciona ejercicios graduales
           - Da pistas y guías sin dar la respuesta directa
           - Fomenta el razonamiento y la reflexión

        4. **REFUERZO Y MOTIVACIÓN**
           - Celebra los logros y comprensión
           - Proporciona retroalimentación positiva específica
           - Sugiere próximos pasos para continuar aprendiendo

        5. **RECURSOS ADICIONALES**
           - Sugiere materiales complementarios apropiados
           - Recomienda actividades de práctica
           - Proporciona consejos de estudio

        CONSIDERACIONES ESPECIALES:
        - Mantén un tono alentador y paciente
        - Si hay áreas de dificultad conocidas, ten especial cuidado
        - Adapta el vocabulario al nivel del estudiante
        - Fomenta preguntas y participación activa
        - Conecta con experiencias de la vida real

        Proporciona una respuesta tutorial completa, personalizada y educativamente sólida.
        """
        
        return prompt
    
    def _parse_tutoring_response(self, response: str) -> Dict[str, Any]:
        """
        Procesa la respuesta tutorial y la estructura
        """
        try:
            return {
                "content": response,
                "format": "tutorial_response",
                "concepts_covered": self._extract_concepts(response),
                "follow_up_suggestions": self._extract_follow_up(response),
                "metadata": {
                    "generated_by": "TutorAgent",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"Error parseando respuesta tutorial: {e}")
            return {
                "content": response,
                "format": "raw_text",
                "error": str(e)
            }
    
    def _extract_concepts(self, response: str) -> List[str]:
        """
        Extrae los conceptos clave cubiertos en la tutoría
        """
        concepts = []
        try:
            # Implementar lógica de extracción de conceptos
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo conceptos: {e}")
        
        return concepts
    
    def _extract_follow_up(self, response: str) -> List[str]:
        """
        Extrae sugerencias de seguimiento de la respuesta
        """
        suggestions = []
        try:
            # Implementar lógica de extracción de sugerencias
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo sugerencias: {e}")
        
        return suggestions
    
    async def explain_concept(
        self, 
        concept: str, 
        student_level: str,
        learning_style: str = "Visual"
    ) -> Dict[str, Any]:
        """
        Explica un concepto específico adaptado al estudiante
        
        Args:
            concept: Concepto a explicar
            student_level: Nivel del estudiante
            learning_style: Estilo de aprendizaje preferido
            
        Returns:
            Explicación personalizada del concepto
        """
        context = {
            "student_grade": student_level,
            "learning_style": learning_style,
            "focus": "concept_explanation"
        }
        
        request = f"Explícame qué es {concept} de manera que pueda entenderlo fácilmente"
        
        return await self.process_request(request, context)
    
    async def help_with_homework(
        self, 
        homework_description: str, 
        student_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ayuda con tareas específicas sin dar respuestas directas
        
        Args:
            homework_description: Descripción de la tarea
            student_context: Contexto del estudiante
            
        Returns:
            Guía para resolver la tarea
        """
        request = f"""
        Necesito ayuda con esta tarea: {homework_description}
        
        No me des la respuesta directa, sino guíame para que pueda resolverla yo mismo.
        """
        
        student_context["focus"] = "homework_assistance"
        
        return await self.process_request(request, student_context)
    
    async def create_study_plan(
        self, 
        subject: str, 
        exam_date: str,
        student_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un plan de estudio personalizado
        
        Args:
            subject: Materia a estudiar
            exam_date: Fecha del examen
            student_context: Contexto del estudiante
            
        Returns:
            Plan de estudio personalizado
        """
        request = f"""
        Ayúdame a crear un plan de estudio para {subject}.
        Mi examen es el {exam_date}.
        
        Necesito un plan que se adapte a mi estilo de aprendizaje y dificultades.
        """
        
        student_context["focus"] = "study_planning"
        
        return await self.process_request(request, student_context)
    
    async def provide_encouragement(
        self, 
        difficulty_area: str, 
        student_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Proporciona motivación y ánimo específico
        
        Args:
            difficulty_area: Área en la que el estudiante tiene dificultades
            student_context: Contexto del estudiante
            
        Returns:
            Mensaje de motivación personalizado
        """
        request = f"""
        Me siento frustrado/a con {difficulty_area}. 
        Siento que no puedo entenderlo y me está costando mucho.
        ¿Puedes ayudarme a sentirme más motivado/a?
        """
        
        student_context["focus"] = "motivation_support"
        
        return await self.process_request(request, student_context)
