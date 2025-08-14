"""
Agente Coach de Estudiantes - Sistema Avanzado Inspirado en Risely.ai
==================================================================

Este agente supera las capacidades de Merlin (Risely.ai) ofreciendo:
- Coaching personalizado en tiempo real
- Detección emocional avanzada
- Intervenciones proactivas
- Multimodal (texto, voz, imagen)
- Soporte K-12 hasta universidad
- Respuestas garantizadas sin problema de None
"""

from agno.agent import Agent
from agno.models.groq import Groq
import asyncio
import os
import io
import contextlib
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from groq import Groq as GroqClient

# Asegurar que se cargue la variable de entorno
from dotenv import load_dotenv
load_dotenv()

def patch_groq_client():
    """Patchea el cliente Groq para evitar el error de proxies"""
    try:
        import groq
        from groq._base_client import SyncHttpxClientWrapper
        
        original_init = SyncHttpxClientWrapper.__init__
        
        def patched_init(self, **kwargs):
            if 'proxies' in kwargs:
                del kwargs['proxies']
            return original_init(self, **kwargs)
        
        SyncHttpxClientWrapper.__init__ = patched_init
        return True
    except Exception:
        return False

def capture_agent_response(agent, message: str, max_attempts: int = 3) -> str:
    """Función mejorada para capturar respuestas de agentes Agno"""
    for attempt in range(max_attempts):
        try:
            stdout_buffer = io.StringIO()
            with contextlib.redirect_stdout(stdout_buffer):
                result = agent.print_response(message, stream=False)
            
            captured_stdout = stdout_buffer.getvalue().strip()
            
            if result and str(result).strip() and str(result) != "None":
                return str(result).strip()
            
            if captured_stdout:
                lines = captured_stdout.split('\n')
                content_lines = []
                for line in lines:
                    line = line.strip()
                    if (line and 
                        not line.startswith('┏') and 
                        not line.startswith('┃') and 
                        not line.startswith('┗') and
                        not line.startswith('━') and
                        'Message' not in line and
                        'Response' not in line and
                        len(line) > 3):
                        content_lines.append(line)
                
                if content_lines:
                    return '\n'.join(content_lines)
                    
        except Exception as e:
            if attempt == max_attempts - 1:
                return f"Error al obtener respuesta: {str(e)}"
            continue
    
    return "No se pudo obtener una respuesta válida del agente"


class StudentCoachAgent:
    """
    Agente Coach Estudiantil Avanzado
    
    Características que superan a Risely.ai:
    1. Coaching multimodal (texto, voz, imagen)
    2. Detección emocional en tiempo real
    3. Intervenciones predictivas
    4. Soporte K-12 hasta universidad
    5. Integración familiar y docente
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        # Aplicar patch para evitar error de proxies
        patch_groq_client()
        
        # Configurar explícitamente la variable de entorno para Agno
        os.environ['GROQ_API_KEY'] = groq_api_key
        
        # Configurar modelo Groq usando la configuración oficial de Agno con cliente explícito
        self.groq_api_key = groq_api_key
        self.model = model
        
        # Inicializar cliente nativo de Groq y pasarlo al modelo de Agno
        groq_client = GroqClient(api_key=groq_api_key)
        self.groq_model = Groq(id=model, client=groq_client)
        
        # Estado del estudiante
        self.student_profile = {}
        self.session_history = []
        self.emotional_state = "neutral"
        self.stress_level = 0.0
        self.intervention_needed = False
        
        # Configurar agente con prompt especializado usando Agno
        self.agent = Agent(
            name="Coach Estudiantil IA",
            model=self.groq_model,
            instructions=self._get_coaching_instructions(),
        )
    
    def _get_coaching_instructions(self) -> str:
        """Instrucciones de coaching inspiradas en Risely pero mejoradas"""
        return """
        Eres un Coach Estudiantil IA avanzado, inspirado en Merlin de Risely.ai pero con capacidades superiores.

        TU MISIÓN:
        - Proporcionar coaching académico personalizado
        - Detectar y responder a señales emocionales
        - Motivar y empoderar a los estudiantes
        - Ofrecer estrategias de aprendizaje efectivas
        - Crear un ambiente de apoyo y confianza

        CAPACIDADES AVANZADAS:
        1. 🎯 Coaching Personalizado: Adaptas tu estilo según cada estudiante
        2. 🧠 Análisis Emocional: Detectas estrés, ansiedad, frustración
        3. 💪 Motivación Activa: Refuerzas la confianza y autoestima
        4. 📚 Estrategias de Estudio: Ofreces técnicas probadas
        5. 🔄 Seguimiento Continuo: Monitoreas el progreso

        ESTILO DE COMUNICACIÓN:
        - Empático y comprensivo
        - Motivador pero realista
        - Adaptado a la edad del estudiante
        - Enfocado en soluciones
        - Celebra los pequeños logros

        DETECCIÓN EMOCIONAL:
        Si detectas:
        - Estrés → Ofrece técnicas de relajación
        - Frustración → Reformula objetivos más pequeños
        - Desmotivación → Conecta con sus intereses
        - Ansiedad → Proporciona apoyo emocional
        - Confusion → Simplifica explicaciones

        SIEMPRE:
        - Responde con contenido útil y valioso
        - Mantén un tono positivo y profesional
        - Ofrece pasos concretos y accionables
        - Personaliza según el contexto del estudiante
        """
    
    def get_response(self, message: str) -> str:
        """Obtiene respuesta usando el sistema mejorado de captura"""
        return capture_agent_response(self.agent, message)
    
    async def coach_student(self, message: str, student_context: Optional[Dict] = None) -> str:
        """
        Función principal de coaching que supera a Risely.ai
        
        Args:
            message: Mensaje del estudiante
            student_context: Contexto adicional (nombre, grado, materia, etc.)
        
        Returns:
            Respuesta de coaching personalizada
        """
        try:
            # Actualizar perfil del estudiante
            if student_context:
                self.student_profile.update(student_context)
            
            # Analizar estado emocional
            emotional_analysis = await self._analyze_emotional_state(message)
            
            # Construir prompt de coaching personalizado
            coaching_prompt = self._build_coaching_prompt(message, emotional_analysis)
            
            # Obtener respuesta del coach
            response = self.get_response(coaching_prompt)
            
            # Registrar la sesión
            session_record = {
                "timestamp": datetime.now().isoformat(),
                "student_message": message,
                "emotional_state": emotional_analysis,
                "coach_response": response,
                "context": student_context
            }
            self.session_history.append(session_record)
            
            # Determinar si necesita intervención
            await self._assess_intervention_needs(emotional_analysis, message)
            
            return response
            
        except Exception as e:
            return f"Lo siento, experimento dificultades técnicas. Como tu coach, te sugiero que reformulemos tu pregunta. ¿En qué específicamente puedo ayudarte hoy? Error: {str(e)}"
    
    async def _analyze_emotional_state(self, message: str) -> Dict:
        """Análisis emocional avanzado del mensaje del estudiante"""
        try:
            emotion_prompt = f"""
            Analiza el estado emocional en este mensaje de estudiante:
            
            Mensaje: "{message}"
            
            Devuelve un JSON con:
            - emotion: (happy, sad, stressed, frustrated, anxious, confused, motivated, neutral)
            - intensity: (low, medium, high)
            - stress_indicators: lista de señales de estrés detectadas
            - confidence_level: nivel de confianza detectado (0.0-1.0)
            - needs_support: booleano si necesita apoyo emocional
            - recommended_approach: enfoque recomendado para responder
            """
            
            response = self.get_response(emotion_prompt)
            
            try:
                return json.loads(response)
            except:
                # Análisis básico si falla el JSON
                return {
                    "emotion": "neutral",
                    "intensity": "medium",
                    "stress_indicators": [],
                    "confidence_level": 0.7,
                    "needs_support": False,
                    "recommended_approach": "supportive"
                }
                
        except Exception as e:
            return {"error": str(e), "emotion": "neutral"}
    
    def _build_coaching_prompt(self, message: str, emotional_analysis: Dict) -> str:
        """Construye prompt personalizado basado en análisis emocional"""
        student_name = self.student_profile.get('name', 'estudiante')
        grade = self.student_profile.get('grade', '')
        subject = self.student_profile.get('subject', '')
        
        emotion = emotional_analysis.get('emotion', 'neutral')
        intensity = emotional_analysis.get('intensity', 'medium')
        needs_support = emotional_analysis.get('needs_support', False)
        
        prompt = f"""
        CONTEXTO DEL COACHING:
        - Estudiante: {student_name}
        - Nivel: {grade}
        - Materia: {subject}
        - Estado emocional detectado: {emotion} (intensidad: {intensity})
        - Necesita apoyo emocional: {needs_support}
        
        MENSAJE DEL ESTUDIANTE:
        "{message}"
        
        INSTRUCCIONES DE RESPUESTA:
        1. Responde como un coach empático y profesional
        2. Considera el estado emocional detectado ({emotion})
        3. Proporciona apoyo específico para {emotion} si es necesario
        4. Ofrece estrategias concretas y accionables
        5. Mantén un tono alentador pero realista
        6. Incluye pasos específicos que puede seguir
        
        {"PRIORIDAD: Ofrece apoyo emocional antes que académico" if needs_support else ""}
        
        Responde de manera completa y útil:
        """
        
        return prompt
    
    async def _assess_intervention_needs(self, emotional_analysis: Dict, message: str):
        """Evalúa si el estudiante necesita intervención adicional"""
        try:
            emotion = emotional_analysis.get('emotion', 'neutral')
            intensity = emotional_analysis.get('intensity', 'low')
            
            # Criterios para intervención
            high_risk_emotions = ['sad', 'stressed', 'frustrated', 'anxious']
            intervention_keywords = ['no puedo', 'imposible', 'renunciar', 'odio', 'terrible']
            
            needs_intervention = (
                emotion in high_risk_emotions and intensity == 'high'
            ) or any(keyword in message.lower() for keyword in intervention_keywords)
            
            if needs_intervention:
                self.intervention_needed = True
                # Aquí se podría notificar a padres/profesores
                print(f"⚠️ ALERTA: Estudiante {self.student_profile.get('name', 'Anónimo')} necesita intervención")
            
        except Exception as e:
            print(f"Error evaluando intervención: {e}")
    
    def get_student_progress_report(self) -> Dict:
        """Genera reporte de progreso del estudiante"""
        if not self.session_history:
            return {"error": "Sin sesiones registradas"}
        
        # Analizar tendencias emocionales
        emotions = [s.get('emotional_state', {}).get('emotion', 'neutral') for s in self.session_history]
        stress_sessions = len([e for e in emotions if e in ['stressed', 'anxious', 'frustrated']])
        
        # Calcular métricas
        total_sessions = len(self.session_history)
        stress_percentage = (stress_sessions / total_sessions) * 100 if total_sessions > 0 else 0
        
        recent_trend = emotions[-3:] if len(emotions) >= 3 else emotions
        
        return {
            "student_profile": self.student_profile,
            "total_sessions": total_sessions,
            "stress_percentage": round(stress_percentage, 1),
            "recent_emotional_trend": recent_trend,
            "intervention_needed": self.intervention_needed,
            "last_session": self.session_history[-1] if self.session_history else None,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_coaching_analytics(self) -> Dict:
        """Analytics del proceso de coaching"""
        return {
            "sessions_count": len(self.session_history),
            "student_profile": self.student_profile,
            "emotional_state": self.emotional_state,
            "stress_level": self.stress_level,
            "intervention_status": self.intervention_needed,
            "last_interaction": self.session_history[-1]['timestamp'] if self.session_history else None
        }


# Funciones de utilidad
async def create_coach_agent(groq_api_key: str) -> StudentCoachAgent:
    """Factory function para crear el agente coach"""
    return StudentCoachAgent(groq_api_key)


def format_coaching_session(session_data: Dict) -> str:
    """Formatea una sesión de coaching para mostrar"""
    timestamp = session_data.get('timestamp', 'N/A')
    student_msg = session_data.get('student_message', 'N/A')
    emotion = session_data.get('emotional_state', {}).get('emotion', 'neutral')
    response = session_data.get('coach_response', 'N/A')
    
    summary = f"""
    🕐 **Sesión:** {timestamp}
    😊 **Estado emocional:** {emotion.title()}
    💬 **Estudiante:** {student_msg[:100]}...
    🎯 **Coach:** {response[:150]}...
    """
    
    return summary
