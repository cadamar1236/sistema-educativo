"""
Configuración del sistema educativo multiagente con Groq y Agno
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración principal del sistema"""
    
    # API Keys
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Configuración de Groq - Usando modelo GPT OSS 20B
    groq_model: str = "openai/gpt-oss-20b"  # Modelo principal actualizado
    model: str = "openai/gpt-oss-20b"  # Alias para compatibilidad
    groq_fast_model: str = "llama-3.1-8b-instant"  # Modelo rápido alternativo
    groq_creative_model: str = "mixtral-8x7b-32768"  # Para tareas creativas
    groq_temperature: float = 0.3  # Más determinístico
    groq_max_tokens: int = 8192
    
    # Directorios
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    upload_dir: Path = data_dir / "uploads"
    temp_dir: Path = data_dir / "temp"
    reports_dir: Path = data_dir / "reports"
    logs_dir: Path = base_dir / "logs"
    vector_db_path: str = str(data_dir / "vector_db")
    
    # ChromaDB y embeddings
    chroma_persist_directory: str = str(data_dir / "chroma")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Servidor
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    
    # Aplicación
    max_file_size: str = "50MB"
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "xlsx", "txt", "md", "pptx"])
    max_tokens: int = 4096
    
    # Agentes
    agent_timeout: int = 300
    max_concurrent_agents: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # === FUNCIONALIDADES ESTILO RISELY.AI MEJORADAS ===
    
    # Personalización de estudiantes (como Risely.ai pero mejor)
    student_profiling_enabled: bool = True
    learning_style_detection: bool = True
    emotional_intelligence_tracking: bool = True
    
    # Sistema de Coaching en tiempo real (inspirado en Merlin de Risely)
    real_time_coaching: bool = True
    nudge_system_enabled: bool = True
    intervention_threshold: float = 0.7  # Cuando intervenir automáticamente
    
    # Analytics avanzados (superando a Risely)
    learning_analytics_enabled: bool = True
    predictive_modeling: bool = True
    parent_teacher_insights: bool = True
    
    # Multimodal capabilities (tu ventaja única)
    voice_interaction: bool = True
    image_analysis: bool = True
    video_processing: bool = True
    
    # Multi-stakeholder (tu diferenciador clave)
    teacher_dashboard: bool = True
    parent_portal: bool = True
    admin_analytics: bool = True
    
    # Gamificación avanzada
    achievement_system: bool = True
    learning_paths: bool = True
    social_learning: bool = True
    
    class Config:
        env_file = [".env", "../.env"]  # Buscar en directorio actual y padre
        case_sensitive = False
        extra = "ignore"  # Ignorar campos extra del .env
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Crear directorios si no existen
        self.create_directories()
    
    def create_directories(self):
        """Crear directorios necesarios"""
        directories = [
            self.data_dir,
            self.upload_dir,
            self.temp_dir,
            self.reports_dir,
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def verify_api_key(self) -> bool:
        """Verificar que la API key esté configurada"""
        return bool(self.groq_api_key and self.groq_api_key.strip())
    
    def get_debug_info(self) -> dict:
        """Obtener información de debug de la configuración"""
        return {
            "groq_api_key_present": bool(self.groq_api_key and self.groq_api_key.strip()),
            "groq_api_key_length": len(self.groq_api_key) if self.groq_api_key else 0,
            "groq_model": self.groq_model,
            "base_dir": str(self.base_dir),
            "env_file_exists": os.path.exists(self.base_dir / ".env"),
            "parent_env_file_exists": os.path.exists(self.base_dir.parent / ".env")
        }


# Instancia global de configuración
settings = Settings()


# Configuración específica de modelos Groq
GROQ_MODELS = {
    "openai/gpt-oss-20b": {
        "name": "GPT OSS 20B",
        "description": "Modelo GPT open source de 20B parámetros - Principal",
        "max_tokens": 8192,
        "use_cases": ["curriculum", "exams", "complex_analysis", "tutoring"]
    },
    "llama-3.3-70b-versatile": {
        "name": "Llama 3.3 70B",
        "description": "Modelo principal para tareas complejas",
        "max_tokens": 32768,
        "use_cases": ["curriculum", "exams", "complex_analysis"]
    },
    "llama-3.1-8b-instant": {
        "name": "Llama 3.1 8B Instant", 
        "description": "Modelo rápido para tareas simples",
        "max_tokens": 8192,
        "use_cases": ["quick_questions", "summaries", "simple_tasks"]
    },
    "llama-3.2-90b-text-preview": {
        "name": "Llama 3.2 90B Preview",
        "description": "Modelo experimental para tareas avanzadas",
        "max_tokens": 8192,
        "use_cases": ["research", "advanced_analysis"]
    },
    "mixtral-8x7b-32768": {
        "name": "Mixtral 8x7B",
        "description": "Modelo multilingüe especializado",
        "max_tokens": 32768,
        "use_cases": ["multilingual", "code_generation"]
    }
}


# Configuración de agentes
AGENT_CONFIGS = {
    "exam_generator": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.7,
        "max_tokens": 4096,
        "memory_enabled": True,
        "tools": [],  # Sin herramientas complejas
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    },
    "curriculum_creator": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.7,
        "max_tokens": 4096,
        "memory_enabled": True,
        "tools": [],
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    },
    "tutor": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.8,
        "max_tokens": 2048,
        "memory_enabled": True,
        "tools": [],
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    },
    "lesson_planner": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.7,
        "max_tokens": 4096,
        "memory_enabled": True,
        "tools": [],
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    },
    "document_analyzer": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.5,
        "max_tokens": 4096,
        "memory_enabled": True,
        "tools": [],
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    },
    "student_coach": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.7,
        "max_tokens": 2048,
        "memory_enabled": True,
        "tools": [],
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    },
    "analytics": {
        "model": "openai/gpt-oss-20b",  # Usar GPT OSS 20B
        "temperature": 0.5,
        "max_tokens": 4096,
        "memory_enabled": True,
        "tools": [],
        "instructions": [
            "Use markdown to format your answers.",
            "IMPORTANTE: Para matemáticas, usa SIEMPRE sintaxis LaTeX:",
            "- Matemáticas en línea: $expresión$ (ejemplo: $f(x) = x^2$)",
            "- Matemáticas en bloque: $$expresión$$ (ejemplo: $$\\frac{df}{dx} = 2x$$)",
            "- NUNCA uses paréntesis (expresión) para matemáticas",
            "- Ejemplos correctos: $y = f(x)$, $f'(x)$, $\\dfrac{df}{dx}$, $$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"
        ]
    }
}


def get_model_config(agent_type: str) -> Dict[str, Any]:
    """
    Obtiene la configuración de modelo para un tipo de agente
    """
    agent_config = AGENT_CONFIGS.get(agent_type, {})
    model_name = agent_config.get("model", settings.groq_model)
    
    return {
        "model": model_name,
        "temperature": agent_config.get("temperature", settings.groq_temperature),
        "max_tokens": agent_config.get("max_tokens", settings.groq_max_tokens),
        "api_key": settings.groq_api_key
    }


def validate_api_keys() -> bool:
    """
    Valida que las API keys necesarias estén configuradas
    """
    if not settings.groq_api_key:
        print("⚠️ GROQ_API_KEY no está configurada")
        print("Obtén tu API key en: https://console.groq.com/keys")
        return False
    
    return True
