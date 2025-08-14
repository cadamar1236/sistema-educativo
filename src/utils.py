"""
Utilidades y herramientas auxiliares
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import json

from src.config import settings


def setup_logging():
    """Configurar sistema de logging"""
    
    # Crear directorio de logs si no existe
    settings.logs_dir.mkdir(exist_ok=True)
    
    # Configurar formato
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(settings.logs_dir / "app.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def save_to_json(data: Dict[str, Any], filename: str, directory: Path = None) -> bool:
    """Guardar datos en archivo JSON"""
    
    try:
        if directory is None:
            directory = settings.data_dir
        
        directory.mkdir(exist_ok=True)
        file_path = directory / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return True
    
    except Exception as e:
        logging.error(f"Error saving JSON file {filename}: {e}")
        return False


def load_from_json(filename: str, directory: Path = None) -> Dict[str, Any]:
    """Cargar datos desde archivo JSON"""
    
    try:
        if directory is None:
            directory = settings.data_dir
        
        file_path = directory / filename
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    
    except Exception as e:
        logging.error(f"Error loading JSON file {filename}: {e}")
        return {}


def generate_report_id() -> str:
    """Generar ID único para reportes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"report_{timestamp}"


def validate_file_extension(filename: str) -> bool:
    """Validar extensión de archivo"""
    extension = filename.split('.')[-1].lower()
    return extension in settings.allowed_extensions


def clean_temp_files(max_age_hours: int = 24):
    """Limpiar archivos temporales antiguos"""
    
    try:
        temp_dir = settings.temp_dir
        current_time = datetime.now()
        
        for file_path in temp_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_age.total_seconds() > max_age_hours * 3600:
                    file_path.unlink()
                    logging.info(f"Deleted old temp file: {file_path}")
    
    except Exception as e:
        logging.error(f"Error cleaning temp files: {e}")


def format_agent_response(content: str, agent_type: str) -> str:
    """Formatear respuesta de agente para mostrar"""
    
    header = f"=== Respuesta del {agent_type.replace('_', ' ').title()} ===\n"
    footer = f"\n=== Fin de respuesta ===\n"
    
    return f"{header}{content}{footer}"


def extract_key_concepts(text: str, max_concepts: int = 10) -> List[str]:
    """Extraer conceptos clave de un texto"""
    
    # Implementación básica - en producción usarías NLP más avanzado
    import re
    
    # Palabras comunes a filtrar
    stop_words = {
        'el', 'la', 'de', 'que', 'y', 'es', 'en', 'un', 'se', 'no', 'te', 'lo', 
        'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las',
        'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas'
    }
    
    # Extraer palabras
    words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text.lower())
    
    # Filtrar y contar
    word_count = {}
    for word in words:
        if word not in stop_words:
            word_count[word] = word_count.get(word, 0) + 1
    
    # Obtener los más frecuentes
    concepts = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    return [concept[0] for concept in concepts[:max_concepts]]


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Estimar tiempo de lectura en minutos"""
    
    word_count = len(text.split())
    reading_time = max(1, round(word_count / words_per_minute))
    
    return reading_time


def create_backup(source_dir: Path, backup_name: str = None) -> bool:
    """Crear backup de directorio"""
    
    try:
        import shutil
        
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = settings.data_dir / "backups" / backup_name
        backup_path.parent.mkdir(exist_ok=True)
        
        shutil.copytree(source_dir, backup_path)
        
        logging.info(f"Backup created: {backup_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitizar nombre de archivo"""
    
    import re
    
    # Remover caracteres no válidos
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limitar longitud
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:95] + ext
    
    return sanitized


def parse_difficulty_level(level_str: str) -> str:
    """Parsear nivel de dificultad"""
    
    level_mapping = {
        'fácil': 'basic',
        'facil': 'basic',
        'básico': 'basic',
        'basico': 'basic',
        'principiante': 'basic',
        'intermedio': 'intermediate',
        'medio': 'intermediate',
        'avanzado': 'advanced',
        'difícil': 'advanced',
        'dificil': 'advanced',
        'experto': 'advanced'
    }
    
    return level_mapping.get(level_str.lower(), 'intermediate')


def format_curriculum_section(title: str, content: List[str], level: int = 1) -> str:
    """Formatear sección de currículum"""
    
    header = "#" * level + f" {title}\n\n"
    
    if isinstance(content, list):
        formatted_content = ""
        for item in content:
            formatted_content += f"- {item}\n"
    else:
        formatted_content = str(content)
    
    return f"{header}{formatted_content}\n"


def calculate_exam_duration(num_questions: int, question_types: List[str]) -> int:
    """Calcular duración estimada de examen"""
    
    # Tiempo base por tipo de pregunta (en minutos)
    time_per_type = {
        'multiple_choice': 1.5,
        'true_false': 1.0,
        'short_answer': 3.0,
        'essay': 10.0,
        'fill_blank': 2.0
    }
    
    # Tiempo promedio
    avg_time = sum(time_per_type.get(qtype, 2.0) for qtype in question_types) / len(question_types)
    
    # Calcular duración total + buffer
    total_time = num_questions * avg_time * 1.2  # 20% buffer
    
    # Redondear a múltiplos de 5
    return max(15, round(total_time / 5) * 5)


# Logging setup
logger = setup_logging()
