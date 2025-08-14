"""
Agente base para el sistema educativo usando Agno framework
Versión mejorada que resuelve el problema de respuestas None
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio
import logging
import os
import io
import contextlib

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.file import FileTools
from agno.tools.reasoning import ReasoningTools
from groq import Groq as GroqClient

from src.config import settings, get_model_config, AGENT_CONFIGS

# Asegurar que se cargue la variable de entorno
from dotenv import load_dotenv
load_dotenv()

def patch_groq_client():
    """Patchea el cliente Groq para evitar el error de proxies"""
    try:
        import groq
        from groq._base_client import SyncHttpxClientWrapper
        
        # Guardar la función original
        original_init = SyncHttpxClientWrapper.__init__
        
        def patched_init(self, **kwargs):
            # Eliminar el parámetro problemático si existe
            if 'proxies' in kwargs:
                del kwargs['proxies']
            # Llamar a la función original sin el parámetro problemático
            return original_init(self, **kwargs)
        
        # Aplicar el patch
        SyncHttpxClientWrapper.__init__ = patched_init
        return True
    except Exception:
        return False

def capture_agent_response(agent, message: str, max_attempts: int = 3) -> str:
    """
    Función mejorada para capturar respuestas de agentes Agno
    que resuelve definitivamente el problema de content: None
    """
    for attempt in range(max_attempts):
        try:
            # Método 1: Usar run() directamente sin decoraciones
            try:
                result = agent.run(message, stream=False)
                if result and str(result).strip() and str(result) != "None":
                    # Limpiar caracteres de decoración si existen
                    clean_result = str(result).strip()
                    clean_result = clean_result.replace('┏', '').replace('┃', '').replace('┗', '').replace('━', '')
                    clean_result = '\n'.join([line.strip() for line in clean_result.split('\n') if line.strip()])
                    if clean_result:
                        return clean_result
            except AttributeError:
                pass
            
            # Método 2: Capturar stdout pero limpiar decoraciones
            stdout_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(stdout_buffer):
                try:
                    result = agent.print_response(message, stream=False)
                except:
                    pass
            
            captured_stdout = stdout_buffer.getvalue().strip()
            
            if captured_stdout:
                # Limpiar todas las decoraciones y caracteres especiales
                clean_output = captured_stdout
                clean_output = clean_output.replace('┏', '').replace('┃', '').replace('┗', '').replace('━', '')
                clean_output = clean_output.replace('│', '').replace('┌', '').replace('└', '').replace('─', '')
                
                # Filtrar líneas útiles
                lines = clean_output.split('\n')
                content_lines = []
                for line in lines:
                    line = line.strip()
                    if (line and 
                        'Message' not in line and
                        'Response' not in line and
                        len(line) > 3 and
                        not line.startswith('=') and
                        not line.startswith('-')):
                        content_lines.append(line)
                
                if content_lines:
                    return '\n'.join(content_lines)
            
            # Método 3: Acceso directo al modelo si disponible
            try:
                if hasattr(agent, 'model'):
                    result3 = agent.model.invoke(message)
                    if result3 and str(result3).strip():
                        return str(result3).strip()
            except:
                pass
                
        except Exception as e:
            if attempt == max_attempts - 1:
                return f"Error al obtener respuesta después de {max_attempts} intentos: {str(e)}"
            continue
    
    return "No se pudo obtener una respuesta válida del agente"

def _fallback_response(groq_api_key: str, request: str, context: Optional[Dict] = None) -> str:
    """Sistema de respaldo usando Groq directamente"""
    try:
        from groq import Groq as GroqClient
        
        client = GroqClient(api_key=groq_api_key)
        
        if context:
            prompt = f"Contexto: {context}\n\nPregunta: {request}\n\nProporciona una respuesta educativa completa y útil:"
        else:
            prompt = f"Pregunta educativa: {request}\n\nRespuesta:"
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system", 
                "content": "Eres un asistente educativo experto. Proporciona respuestas claras, educativas y útiles."
            }, {
                "role": "user", 
                "content": prompt
            }],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Respuesta educativa básica para: {request}\n\nLo siento, experimento dificultades técnicas, pero puedo ayudarte de forma básica. ¿Podrías reformular tu pregunta?"


class BaseEducationalAgent(ABC):
    """
    Clase base para todos los agentes educativos del sistema.
    Utiliza Agno para gestión de memoria, herramientas y coordinación.
    Incluye solución mejorada para el problema de respuestas None.
    """
    
    def __init__(
        self,
        agent_type: str,
        name: str,
        description: str,
        groq_api_key: str = None,
        custom_instructions: Optional[List[str]] = None,
        tools: Optional[List[Any]] = None
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{agent_type}")
        
        # API Key
        self.groq_api_key = groq_api_key or settings.groq_api_key or os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY es requerida")
        
        # Obtener configuración específica del agente
        self.config = get_model_config(agent_type)
        agent_config = AGENT_CONFIGS.get(agent_type, {})
        
        # Configurar modelo Groq usando un cliente explícito para evitar el error 'proxies'
        try:
            # Aplicar patch para evitar error de proxies
            patch_groq_client()
            
            # Asegurar variable de entorno para librerías que la lean automáticamente
            os.environ["GROQ_API_KEY"] = self.groq_api_key
            
            # Crear cliente Groq explícito
            groq_client = GroqClient(api_key=self.groq_api_key)
            
            # Crear modelo con cliente explícito
            self.model = Groq(
                id=self.config.get("model", "llama-3.1-8b-instant"),
                client=groq_client,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 1500)
            )
            
        except Exception as e:
            self.logger.error(f"Error configurando modelo Groq: {e}")
            raise
        
        # Combinar instrucciones base con personalizadas
        base_instructions = agent_config.get("instructions", [])
        instructions = base_instructions + (custom_instructions or [])
        
        # Herramientas base
        base_tools = []
        if agent_config.get("enable_file_tools", False):
            base_tools.append(FileTools())
        if agent_config.get("enable_reasoning_tools", True):
            base_tools.append(ReasoningTools())
        
        # Combinar con herramientas personalizadas
        all_tools = base_tools + (tools or [])
        
        # Crear agente Agno
        try:
            self.agent = Agent(
                name=self.name,
                model=self.model,
                tools=all_tools,
                instructions="\n".join(instructions) if instructions else None,
                show_tool_calls=True,
                markdown=True
            )
        except Exception as e:
            self.logger.error(f"Error creando agente: {e}")
            raise
        
        # Estado del agente
        self.is_initialized = True
        self.conversation_history = []
        
        self.logger.info(f"Agente {self.name} inicializado correctamente")
    
    def get_response(self, message: str) -> str:
        """
        Método mejorado para obtener respuestas que resuelve el problema de None
        """
        return capture_agent_response(self.agent, message)
    
    def process_request(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Procesa una solicitud y garantiza respuesta válida
        """
        try:
            # Construir prompt con contexto
            if context:
                prompt = f"""
Contexto educativo: {context}

Solicitud del estudiante: {request}

Instrucciones:
- Proporciona una respuesta educativa completa y útil
- Explica conceptos de manera clara
- Incluye ejemplos cuando sea apropiado
- Mantén un tono amigable y motivador
- IMPORTANTE: Responde siempre con contenido educativo valioso
"""
            else:
                prompt = f"""
Solicitud educativa: {request}

Proporciona una respuesta educativa completa, clara y útil.
IMPORTANTE: Siempre responde con contenido educativo valioso.
"""
            
            # Obtener respuesta garantizada
            response = self.get_response(prompt)
            
            # Validar que la respuesta no esté vacía
            if not response or response.strip() == "" or "Error" in response:
                # Fallback: usar cliente Groq directo
                response = _fallback_response(self.groq_api_key, request, context)
            
            # Guardar en historial
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "request": request,
                "response": response,
                "context": context
            })
            
            return {
                "success": True,
                "content": response,
                "format": "educational_response",
                "agent_type": self.agent_type,
                "metadata": {
                    "generated_by": self.__class__.__name__,
                    "timestamp": datetime.now().isoformat(),
                    "has_valid_content": bool(response and len(response.strip()) > 10)
                }
            }
            
        except Exception as e:
            # En caso de error, usar fallback
            fallback_response = _fallback_response(self.groq_api_key, request, context)
            
            return {
                "success": False,
                "content": fallback_response,
                "error": str(e),
                "format": "fallback_response",
                "agent_type": self.agent_type,
                "metadata": {
                    "generated_by": "Fallback System",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def process_request_async(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Versión asíncrona de process_request"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.process_request, request, context
        )
    
    def add_to_memory(self, key: str, value: Any) -> None:
        """Añade información a la memoria del agente"""
        try:
            if hasattr(self.agent, 'memory') and self.agent.memory:
                self.agent.memory.upsert(key, value)
        except Exception as e:
            self.logger.warning(f"No se pudo añadir a memoria: {e}")
    
    def get_memory(self, key: str) -> Optional[Any]:
        """Obtiene información de la memoria del agente"""
        try:
            if hasattr(self.agent, 'memory') and self.agent.memory:
                return self.agent.memory.get(key)
        except Exception as e:
            self.logger.warning(f"No se pudo obtener de memoria: {e}")
        return None
    
    def get_conversation_history(self) -> List[Dict]:
        """Obtiene el historial de conversación"""
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Limpia el historial de conversación"""
        self.conversation_history = []
    
    @abstractmethod
    async def process_specific_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud específica del agente.
        Debe ser implementado por cada agente específico.
        
        Args:
            request: La solicitud a procesar
            
        Returns:
            Dict con la respuesta del agente
        """
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Obtiene información del agente"""
        return {
            "name": self.name,
            "type": self.agent_type,
            "description": self.description,
            "is_initialized": self.is_initialized,
            "conversation_count": len(self.conversation_history)
        }
