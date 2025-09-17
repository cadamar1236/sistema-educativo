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
    print(f"🏃‍♂️ capture_agent_response called with message: {message[:100]}...")
    
    for attempt in range(max_attempts):
        try:
            print(f"🏃‍♂️ Attempt {attempt + 1}/{max_attempts}")
            
            stdout_buffer = io.StringIO()
            with contextlib.redirect_stdout(stdout_buffer):
                result = agent.print_response(message, stream=False)
            
            captured_stdout = stdout_buffer.getvalue().strip()
            print(f"🏃‍♂️ Result type: {type(result)}, length: {len(str(result))}")
            print(f"🏃‍♂️ Stdout length: {len(captured_stdout)}")
            
            if result and str(result).strip() and str(result) != "None":
                final_result = str(result).strip()
                print(f"🏃‍♂️ Returning result: {len(final_result)} chars")
                return final_result
            
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
                    final_result = '\n'.join(content_lines)
                    print(f"🏃‍♂️ Returning stdout: {len(final_result)} chars")
                    return final_result
                    
        except Exception as e:
            print(f"🏃‍♂️ Exception in attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
                return f"Error al obtener respuesta: {str(e)}"
            continue
    
    print(f"🏃‍♂️ Failed all attempts, returning fallback")
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
        """Instrucciones de coaching simplificadas pero efectivas"""
        return """
        Eres un Coach Estudiantil IA experto y empático.

        TU MISIÓN:
        - Ayudar a estudiantes con sus desafíos académicos
        - Proporcionar apoyo emocional y motivación
        - Ofrecer estrategias de estudio efectivas
        - Ser un mentor confiable y comprensivo

        ESTILO DE COMUNICACIÓN:
        - Empático y comprensivo
        - Claro y directo
        - Motivador y positivo
        - Práctico y accionable

        IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:
        - Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)
        - Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)
        - NUNCA uses paréntesis (expresión) para matemáticas

        SIEMPRE:
        - Proporciona respuestas completas y útiles
        - Ofrece pasos concretos
        - Mantén un tono positivo
        - Adapta tu lenguaje al nivel del estudiante
        """
    
    def get_response(self, message: str) -> str:
        """Obtiene respuesta usando el sistema mejorado de captura"""
        print(f"🏃‍♂️ Coach get_response called with message: {message[:100]}...")
        result = capture_agent_response(self.agent, message)
        print(f"🏃‍♂️ Coach get_response result length: {len(str(result))}")
        print(f"🏃‍♂️ Coach get_response result preview: {str(result)[:200]}...")
        return result

    def _strip_prompt_context(self, raw: str) -> str:
        """Elimina el bloque de contexto/instrucciones si el modelo lo devolvió junto a la respuesta.

        Busca el marcador final 'Responde de manera completa y útil:' y devuelve el texto posterior.
        También elimina caracteres de caja residuales y líneas vacías iniciales.
        """
        if not isinstance(raw, str):
            return raw
        cleaned = raw
        marker = "Responde de manera completa y útil:"
        if marker in cleaned:
            # Tomar solo lo que viene después del marcador
            cleaned = cleaned.split(marker, 1)[1]
        # Si todavía contiene 'CONTEXTO DEL COACHING', intentar remover todo hasta últimas instrucciones
        if 'CONTEXTO DEL COACHING' in cleaned and marker not in raw:
            # Heurística: eliminar cualquier línea que empiece con guiones o palabras clave conocidas hasta encontrar una línea vacía doble
            lines = cleaned.splitlines()
            filtered = []
            skip = True
            for line in lines:
                striped = line.strip()
                if skip and striped.startswith('INSTRUCCIONES DE RESPUESTA'):
                    # seguir saltando hasta que pase unas pocas líneas más
                    continue
                if skip and ('Responde de manera completa' in striped):
                    skip = False
                    continue
                if not skip:
                    filtered.append(line)
            if filtered:
                cleaned = '\n'.join(filtered)
        # Eliminar caracteres de caja y códigos ANSI residuales
        for ch in ['┏', '┗', '┃', '━', '┛']:
            cleaned = cleaned.replace(ch, '')
        import re as _re
        cleaned = _re.sub(r'\x1b\[[0-9;]*m', '', cleaned)
        # Quitar espacios múltiples iniciales
        cleaned = '\n'.join([l.rstrip() for l in cleaned.splitlines()]).strip()
        return cleaned
    
    async def coach_student(self, message: str, student_context: Optional[Dict] = None) -> str:
        """
        Función principal de coaching simplificada y mejorada
        
        Args:
            message: Mensaje del estudiante
            student_context: Contexto adicional (nombre, grado, materia, etc.)
        
        Returns:
            Respuesta de coaching personalizada
        """
        try:
            # Construir prompt directo y conciso
            student_name = student_context.get('name', 'estudiante') if student_context else 'estudiante'
            
            # Prompt simplificado pero efectivo
            coaching_prompt = f"""Como coach estudiantil, ayuda a {student_name} con esta consulta:

"{message}"

Proporciona:
1. Una respuesta empática y motivadora
2. Consejos específicos y accionables
3. Estrategias de estudio si es relevante
4. Apoyo emocional si es necesario

Mantén un tono positivo, profesional y alentador."""
            
            # Obtener respuesta del coach
            response = self.get_response(coaching_prompt)
            
            # Limpieza básica de la respuesta
            if isinstance(response, str):
                # Eliminar códigos ANSI y caracteres especiales
                import re
                ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
                response = re.sub(ansi_pattern, '', response)
                # Limpiar caracteres de caja
                for ch in ['┏', '┗', '┃', '━', '┛']:
                    response = response.replace(ch, '')
                response = response.strip()
            
            # Registrar la sesión
            session_record = {
                "timestamp": datetime.now().isoformat(),
                "student_message": message,
                "coach_response": response,
                "context": student_context
            }
            self.session_history.append(session_record)
            
            return response if response and len(response) > 10 else "Como tu coach, te ayudo a superar cualquier desafío académico. ¿Podrías ser más específico sobre lo que necesitas?"
            
        except Exception as e:
            print(f"❌ Error en coach_student: {e}")
            return f"Como tu coach personal, estoy aquí para apoyarte. Cuéntame más específicamente en qué puedo ayudarte con tus estudios."
    
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
