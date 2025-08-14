"""
Agente especializado en análisis de documentos educativos
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime
import os

from agno.tools.reasoning import ReasoningTools
from agno.tools.file import FileTools
from ..base_agent import BaseEducationalAgent


class DocumentAnalyzerAgent(BaseEducationalAgent):
    """
    Agente especializado en análisis y procesamiento de documentos educativos.
    Extrae información relevante, genera resúmenes y responde preguntas sobre contenido.
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        custom_instructions = [
            "Especialízate en analizar documentos educativos de manera profunda",
            "Extrae información clave, conceptos principales y detalles relevantes",
            "Genera resúmenes claros y estructurados",
            "Identifica objetivos de aprendizaje, actividades y evaluaciones",
            "Adapta el análisis al contexto educativo específico",
            "Proporciona insights pedagógicos sobre el contenido",
            "Responde preguntas específicas sobre los documentos",
            "Sugiere aplicaciones prácticas del contenido analizado"
        ]
        
        tools = [
            ReasoningTools(add_instructions=True),
            FileTools()
        ]
        
        super().__init__(
            agent_type="document_analyzer",
            name="Analizador de Documentos",
            description="Especialista en análisis y procesamiento de documentos educativos",
            groq_api_key=groq_api_key,
            custom_instructions=custom_instructions,
            tools=tools
        )
    
    async def process_specific_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud específica del analizador de documentos
        
        Args:
            request: Solicitud con parámetros del análisis
            
        Returns:
            Dict con el análisis del documento
        """
        try:
            document_type = request.get('document_type', 'general')
            analysis_type = request.get('analysis_type', 'summary')
            content = request.get('content', '')
            question = request.get('question', 'Analiza este documento')
            
            # Construir contexto del análisis
            analysis_context = {
                "document_type": document_type,
                "analysis_type": analysis_type,
                "focus": "document_analysis"
            }
            
            # Crear prompt para el análisis
            if content:
                analysis_request = f"Analiza el siguiente documento ({document_type}): {content[:1000]}... Tipo de análisis: {analysis_type}. {question}"
            else:
                analysis_request = f"Realiza un análisis de documento tipo {analysis_type}: {question}"
            
            # Usar el método base mejorado para procesar
            response = self.process_request(analysis_request, analysis_context)
            
            return {
                "success": True,
                "content": response.get('content', ''),
                "format": "analysis_response",
                "analysis_details": {
                    "document_type": document_type,
                    "analysis_type": analysis_type,
                    "content_length": len(content) if content else 0
                },
                "concepts_covered": self._extract_analysis_concepts(response.get('content', '')),
                "follow_up_suggestions": [
                    "¿Quieres un análisis más profundo?",
                    "¿Necesitas extraer información específica?",
                    "¿Te gustaría comparar con otros documentos?"
                ],
                "metadata": {
                    "generated_by": "DocumentAnalyzerAgent",
                    "timestamp": datetime.now().isoformat(),
                    "analysis_type": analysis_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Lo siento, experimento dificultades técnicas analizando el documento. ¿Podrías proporcionar más detalles sobre el análisis que necesitas?",
                "error": str(e),
                "format": "error_response"
            }
    
    def _extract_analysis_concepts(self, content: str) -> list:
        """Extrae conceptos del análisis generado"""
        if not content:
            return []
        
        # Palabras clave relacionadas con análisis de documentos
        analysis_keywords = [
            "resumen", "concepto", "idea principal", "estructura",
            "objetivo", "metodología", "conclusión", "evidencia",
            "argumento", "datos", "información"
        ]
        
        concepts = []
        for keyword in analysis_keywords:
            if keyword in content.lower():
                concepts.append(keyword.title())
        
        return list(set(concepts))[:5]  # Máximo 5 conceptos únicos
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una solicitud de análisis de documento
        
        Args:
            request: Solicitud específica de análisis
            context: Contexto adicional (archivo, tipo de análisis, etc.)
            
        Returns:
            Dict con el análisis del documento
        """
        try:
            start_time = datetime.now()
            
            # Extraer parámetros del contexto
            document_path = context.get("document_path", "") if context else ""
            document_type = context.get("document_type", "general") if context else "general"
            analysis_type = context.get("analysis_type", "comprehensive") if context else "comprehensive"
            target_audience = context.get("target_audience", "general") if context else "general"
            
            # Construir prompt estructurado
            prompt = self._build_analysis_prompt(
                request, document_path, document_type, 
                analysis_type, target_audience
            )
            
            # Generar análisis usando el agente
            response = await asyncio.to_thread(
                self.agent.print_response,
                prompt,
                stream=False
            )
            
            # Procesar y estructurar la respuesta
            analysis_data = self._parse_analysis_response(response)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "analysis": analysis_data,
                "document_path": document_path,
                "document_type": document_type,
                "analysis_type": analysis_type,
                "processing_time": processing_time,
                "generated_at": end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando documento: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    def _build_analysis_prompt(
        self, 
        request: str, 
        document_path: str, 
        document_type: str,
        analysis_type: str, 
        target_audience: str
    ) -> str:
        """
        Construye un prompt estructurado para el análisis de documento
        """
        analysis_types = {
            "comprehensive": "Análisis completo y detallado",
            "summary": "Resumen ejecutivo del contenido",
            "educational_value": "Evaluación del valor educativo",
            "concept_extraction": "Extracción de conceptos clave",
            "question_answering": "Respuesta a preguntas específicas"
        }
        
        prompt = f"""
        ANÁLISIS DE DOCUMENTO EDUCATIVO

        Solicitud específica:
        {request}

        PARÁMETROS DEL ANÁLISIS:
        - Documento: {document_path if document_path else "Contenido proporcionado"}
        - Tipo de documento: {document_type}
        - Tipo de análisis: {analysis_type} ({analysis_types.get(analysis_type, 'análisis general')})
        - Audiencia objetivo: {target_audience}

        ESTRUCTURA DEL ANÁLISIS REQUERIDA:

        1. **INFORMACIÓN GENERAL DEL DOCUMENTO**
           - Título y autor (si aplica)
           - Tipo de documento y formato
           - Audiencia objetivo identificada
           - Propósito educativo principal

        2. **RESUMEN EJECUTIVO**
           - Síntesis del contenido principal
           - Puntos clave destacados
           - Mensaje principal del documento

        3. **ANÁLISIS DE CONTENIDO**
           - Temas principales abordados
           - Conceptos clave identificados
           - Teorías o metodologías mencionadas
           - Datos, estadísticas o evidencias relevantes

        4. **ESTRUCTURA Y ORGANIZACIÓN**
           - Cómo está organizado el contenido
           - Secuencia lógica de ideas
           - Uso de elementos visuales (gráficos, tablas, etc.)
           - Claridad en la presentación

        5. **VALOR EDUCATIVO**
           - Objetivos de aprendizaje implícitos o explícitos
           - Nivel educativo apropiado
           - Competencias que desarrolla
           - Aplicaciones prácticas del contenido

        6. **FORTALEZAS Y LIMITACIONES**
           - Aspectos positivos del documento
           - Áreas de mejora identificadas
           - Posibles sesgos o limitaciones
           - Actualidad del contenido

        7. **CONCEPTOS CLAVE EXTRAÍDOS**
           - Lista de conceptos principales
           - Definiciones importantes
           - Términos técnicos relevantes
           - Relaciones entre conceptos

        8. **PREGUNTAS DE COMPRENSIÓN SUGERIDAS**
           - Preguntas de nivel básico
           - Preguntas de análisis
           - Preguntas de aplicación
           - Preguntas de evaluación crítica

        9. **RECURSOS RELACIONADOS**
           - Bibliografía mencionada
           - Recursos adicionales sugeridos
           - Conexiones con otros materiales educativos

        10. **RECOMENDACIONES DE USO**
            - Cómo utilizar este documento en enseñanza
            - Actividades complementarias sugeridas
            - Adaptaciones para diferentes niveles
            - Integración con currículum

        INSTRUCCIONES ESPECÍFICAS:
        - Mantén un enfoque educativo en todo el análisis
        - Identifica oportunidades de aprendizaje
        - Sugiere aplicaciones prácticas
        - Considera diferentes estilos de aprendizaje
        - Proporciona insights pedagógicos valiosos

        Realiza un análisis profundo, estructurado y educativamente útil del documento.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del análisis y la estructura
        """
        try:
            return {
                "content": response,
                "format": "structured_analysis",
                "key_concepts": self._extract_key_concepts(response),
                "summary": self._extract_summary(response),
                "educational_value": self._assess_educational_value(response),
                "metadata": {
                    "generated_by": "DocumentAnalyzerAgent",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"Error parseando análisis: {e}")
            return {
                "content": response,
                "format": "raw_text",
                "error": str(e)
            }
    
    def _extract_key_concepts(self, response: str) -> List[str]:
        """
        Extrae conceptos clave del análisis
        """
        concepts = []
        try:
            # Implementar lógica de extracción de conceptos
            pass
        except Exception as e:
            self.logger.error(f"Error extrayendo conceptos: {e}")
        
        return concepts
    
    def _extract_summary(self, response: str) -> str:
        """
        Extrae el resumen del análisis
        """
        try:
            # Implementar lógica de extracción de resumen
            return "Resumen no disponible"
        except Exception as e:
            self.logger.error(f"Error extrayendo resumen: {e}")
            return "Error extrayendo resumen"
    
    def _assess_educational_value(self, response: str) -> Dict[str, Any]:
        """
        Evalúa el valor educativo del documento
        """
        try:
            # Implementar lógica de evaluación educativa
            return {
                "score": 0.0,
                "criteria": [],
                "recommendations": []
            }
        except Exception as e:
            self.logger.error(f"Error evaluando valor educativo: {e}")
            return {"error": str(e)}
    
    async def summarize_document(
        self, 
        document_path: str,
        summary_length: str = "medium"
    ) -> Dict[str, Any]:
        """
        Genera un resumen del documento
        
        Args:
            document_path: Ruta al documento
            summary_length: Longitud del resumen (short, medium, long)
            
        Returns:
            Resumen del documento
        """
        context = {
            "document_path": document_path,
            "analysis_type": "summary",
            "summary_length": summary_length
        }
        
        length_descriptions = {
            "short": "un resumen breve de 1-2 párrafos",
            "medium": "un resumen detallado de 3-5 párrafos", 
            "long": "un resumen extenso con todos los puntos importantes"
        }
        
        request = f"""
        Genera {length_descriptions.get(summary_length, 'un resumen')} del documento.
        Incluye los puntos más importantes y la información clave.
        """
        
        return await self.process_request(request, context)
    
    async def extract_learning_objectives(
        self, 
        document_path: str
    ) -> Dict[str, Any]:
        """
        Extrae objetivos de aprendizaje del documento
        
        Args:
            document_path: Ruta al documento
            
        Returns:
            Objetivos de aprendizaje identificados
        """
        context = {
            "document_path": document_path,
            "analysis_type": "objective_extraction"
        }
        
        request = """
        Identifica y extrae todos los objetivos de aprendizaje presentes en el documento.
        Si no están explícitos, infiere objetivos basados en el contenido.
        Organiza los objetivos por nivel (conocimiento, comprensión, aplicación, etc.).
        """
        
        return await self.process_request(request, context)
    
    async def compare_documents(
        self, 
        document_paths: List[str],
        comparison_criteria: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compara múltiples documentos educativos
        
        Args:
            document_paths: Lista de rutas a documentos
            comparison_criteria: Criterios específicos de comparación
            
        Returns:
            Análisis comparativo
        """
        if not comparison_criteria:
            comparison_criteria = [
                "contenido", "nivel educativo", "metodología", 
                "valor pedagógico", "actualidad"
            ]
        
        context = {
            "document_paths": document_paths,
            "analysis_type": "comparative",
            "criteria": comparison_criteria
        }
        
        request = f"""
        Compara los siguientes documentos basándote en estos criterios:
        {', '.join(comparison_criteria)}
        
        Documentos: {', '.join(document_paths)}
        
        Proporciona un análisis comparativo detallado destacando:
        - Similitudes y diferencias
        - Fortalezas de cada documento
        - Recomendaciones de uso
        """
        
        return await self.process_request(request, context)
    
    async def answer_document_question(
        self, 
        document_path: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Responde una pregunta específica sobre un documento
        
        Args:
            document_path: Ruta al documento
            question: Pregunta específica
            
        Returns:
            Respuesta basada en el documento
        """
        context = {
            "document_path": document_path,
            "analysis_type": "question_answering",
            "specific_question": question
        }
        
        request = f"""
        Basándote únicamente en el contenido del documento, responde la siguiente pregunta:
        
        {question}
        
        Proporciona una respuesta detallada y cita las partes relevantes del documento.
        Si la información no está en el documento, indícalo claramente.
        """
        
        return await self.process_request(request, context)
