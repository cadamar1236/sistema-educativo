"""
Agent base mejorado para el sistema educativo
"""

from typing import Dict, Any, Optional, List
import json
import re
from datetime import datetime
import asyncio

class EnhancedEducationalAgent:
    """Agdente educativo mejorado con capacidades avanzadas"""
    
    def __init__(self, agent_type: str = "enhanced", agent_name: str = "Enhanced Agent", config: Optional[Dict] = None):
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.config = config or {}
        self.conversation_history = []
        self.capabilities = [
            "respuestas_educativas",
            "analisis_texto",
            "generacion_contenido",
            "soporte_multiidioma",
            "tracking_progreso"
        ]
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Procesar mensaje del usuario y generar respuesta educativa"""
        try:
            # Limpiar y preparar el mensaje
            cleaned_message = self._clean_message(message)
            
            # Agregar a historial
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "message": cleaned_message,
                "context": context or {}
            })
            
            # Generar respuesta basada en el tipo de consulta
            response = await self._generate_educational_response(cleaned_message, context)
            
            return response
            
        except Exception as e:
            return f"⚠️ Error procesando mensaje: {str(e)}"
    
    def _clean_message(self, message: str) -> str:
        """Limpiar y formatear mensaje de entrada"""
        if not message:
            return ""
        
        # Eliminar caracteres especiales y normalizar espacios
        cleaned = re.sub(r'\s+', ' ', message.strip())
        return cleaned
    
    async def _generate_educational_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generar respuesta educativa apropiada"""
        
        # Determinar tipo de consulta
        query_type = self._classify_query(message)
        
        if query_type == "pregunta_academica":
            return await self._handle_academic_question(message, context)
        elif query_type == "solicitud_explicacion":
            return await self._handle_explanation_request(message, context)
        elif query_type == "evaluacion":
            return await self._handle_evaluation_request(message, context)
        elif query_type == "planificacion":
            return await self._handle_planning_request(message, context)
        else:
            return await self._handle_general_query(message, context)
    
    def _classify_query(self, message: str) -> str:
        """Clasificar tipo de consulta educativa"""
        message_lower = message.lower()
        
        # Palabras clave para diferentes tipos de consultas
        academic_keywords = ["qué es", "define", "explica", "concepto", "teoría", "fórmula"]
        explanation_keywords = ["cómo", "por qué", "pasos", "proceso", "método"]
        evaluation_keywords = ["examen", "prueba", "evaluación", "ejercicio", "problema"]
        planning_keywords = ["plan", "cronograma", "organizar", "estudiar", "preparar"]
        
        if any(keyword in message_lower for keyword in academic_keywords):
            return "pregunta_academica"
        elif any(keyword in message_lower for keyword in explanation_keywords):
            return "solicitud_explicacion"
        elif any(keyword in message_lower for keyword in evaluation_keywords):
            return "evaluacion"
        elif any(keyword in message_lower for keyword in planning_keywords):
            return "planificacion"
        else:
            return "consulta_general"
    
    async def _handle_academic_question(self, message: str, context: Optional[Dict] = None) -> str:
        """Manejar preguntas académicas"""
        return f"""📚 **Respuesta Académica**

**Consulta:** {message}

📖 Esta es una pregunta académica importante. Te ayudo a comprenderla:

🔍 **Análisis del tema:**
- Concepto fundamental en el área de estudio
- Requiere comprensión teórica y práctica
- Importante para el desarrollo del conocimiento

💡 **Puntos clave a considerar:**
- Definiciones precisas
- Ejemplos prácticos
- Aplicaciones reales
- Conexiones con otros conceptos

📝 **Recomendación:** 
Para una comprensión completa, te sugiero revisar material adicional y practicar con ejercicios relacionados.

¿Te gustaría que profundice en algún aspecto específico?"""
    
    async def _handle_explanation_request(self, message: str, context: Optional[Dict] = None) -> str:
        """Manejar solicitudes de explicación"""
        return f"""🎯 **Explicación Detallada**

**Tu consulta:** {message}

📋 **Pasos para entender el proceso:**

1️⃣ **Primer paso:** Identificar los elementos clave
2️⃣ **Segundo paso:** Analizar las relaciones
3️⃣ **Tercer paso:** Aplicar el conocimiento
4️⃣ **Cuarto paso:** Verificar la comprensión

🔬 **Metodología recomendada:**
- Partir de lo conocido hacia lo desconocido
- Usar ejemplos concretos
- Practicar con casos similares
- Buscar patrones y conexiones

✅ **Para verificar tu comprensión:**
- Explica el proceso con tus propias palabras
- Aplica en un ejemplo diferente
- Identifica posibles variaciones

¿Hay algún paso específico que necesitas que clarifique más?"""
    
    async def _handle_evaluation_request(self, message: str, context: Optional[Dict] = None) -> str:
        """Manejar solicitudes de evaluación"""
        return f"""📊 **Soporte para Evaluación**

**Área de evaluación:** {message}

🎯 **Estrategia de preparación:**

📚 **Revisión de contenidos:**
- Conceptos fundamentales
- Fórmulas y definiciones clave
- Ejemplos y casos prácticos

🧠 **Técnicas de estudio:**
- Resúmenes estructurados
- Mapas conceptuales
- Práctica con ejercicios
- Autoevaluación continua

⏰ **Planificación temporal:**
- Distribución de temas por sesiones
- Tiempo para repaso
- Práctica de exámenes anteriores

💪 **Consejos para el día del examen:**
- Lectura cuidadosa de instrucciones
- Gestión efectiva del tiempo
- Revisión final de respuestas

¿Te gustaría que te ayude a crear un plan de estudio específico?"""
    
    async def _handle_planning_request(self, message: str, context: Optional[Dict] = None) -> str:
        """Manejar solicitudes de planificación"""
        return f"""📅 **Plan de Estudio Personalizado**

**Objetivo:** {message}

🗓️ **Estructura de planificación:**

**Fase 1: Diagnóstico (Semana 1)**
- Evaluación de conocimientos previos
- Identificación de fortalezas y áreas de mejora
- Definición de objetivos específicos

**Fase 2: Desarrollo (Semanas 2-4)**
- Estudio sistemático de contenidos
- Práctica regular con ejercicios
- Seguimiento de progreso

**Fase 3: Consolidación (Semana 5)**
- Repaso integral
- Resolución de dudas
- Preparación final

📈 **Métricas de seguimiento:**
- Tiempo dedicado por tema
- Nivel de comprensión alcanzado
- Resultados en autoevaluaciones

🎯 **Ajustes personalizados:**
- Adaptación según tu ritmo de aprendizaje
- Enfoque en áreas que requieren más atención
- Flexibilidad para cambios necesarios

¿Te gustaría que detalle alguna fase específica del plan?"""
    
    async def _handle_general_query(self, message: str, context: Optional[Dict] = None) -> str:
        """Manejar consultas generales"""
        return f"""💬 **Respuesta Educativa General**

**Tu consulta:** {message}

👋 Como tu asistente educativo, estoy aquí para ayudarte con:

📚 **Apoyo académico:**
- Explicaciones de conceptos
- Resolución de dudas
- Guía en metodologías de estudio

🎯 **Planificación educativa:**
- Organización de horarios de estudio
- Estrategias de aprendizaje
- Preparación para evaluaciones

💡 **Recursos adicionales:**
- Sugerencias de material de estudio
- Técnicas de memorización
- Métodos de autoevaluación

🤝 **Personalización:**
- Adaptación a tu estilo de aprendizaje
- Seguimiento de tu progreso
- Ajustes según tus necesidades

¿Hay algo específico en lo que pueda ayudarte mejor? ¡Estoy aquí para apoyar tu proceso de aprendizaje!"""
    
    def get_conversation_history(self) -> List[Dict]:
        """Obtener historial de conversación"""
        return self.conversation_history
    
    def clear_history(self):
        """Limpiar historial de conversación"""
        self.conversation_history = []
    
    def get_capabilities(self) -> List[str]:
        """Obtener lista de capacidades del agente"""
        return self.capabilities
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Obtener información del agente"""
        return {
            "type": self.agent_type,
            "name": self.agent_name,
            "capabilities": self.capabilities,
            "conversation_length": len(self.conversation_history),
            "config": self.config,
            "status": "active"
        }
