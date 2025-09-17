"""
Modelos de datos para el sistema educativo
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Tipos de agentes disponibles"""
    EXAM_GENERATOR = "exam_generator"
    CURRICULUM_CREATOR = "curriculum_creator"
    TUTOR = "tutor"
    PERFORMANCE_ANALYZER = "performance_analyzer"
    LESSON_PLANNER = "lesson_planner"


class DocumentType(str, Enum):
    """Tipos de documentos soportados"""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    MARKDOWN = "md"


class DifficultyLevel(str, Enum):
    """Niveles de dificultad"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionType(str, Enum):
    """Tipos de preguntas para exámenes"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_BLANK = "fill_blank"


class Document(BaseModel):
    """Modelo para documentos subidos"""
    id: str
    filename: str
    file_type: DocumentType
    content: str
    metadata: Dict[str, Any] = {}
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed: bool = False
    subject: Optional[str] = None
    grade_level: Optional[str] = None


class Question(BaseModel):
    """Modelo para preguntas de examen"""
    id: str
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None  # Para multiple choice
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: DifficultyLevel
    points: int = 1
    topic: Optional[str] = None


class Exam(BaseModel):
    """Modelo para exámenes generados"""
    id: str
    title: str
    subject: str
    grade_level: str
    questions: List[Question]
    total_points: int
    duration_minutes: int
    instructions: str
    created_at: datetime = Field(default_factory=datetime.now)
    created_by_agent: bool = True


class CurriculumUnit(BaseModel):
    """Unidad de currículum"""
    id: str
    title: str
    description: str
    objectives: List[str]
    topics: List[str]
    duration_weeks: int
    prerequisites: List[str] = []
    resources: List[str] = []


class Curriculum(BaseModel):
    """Modelo para currículum completo"""
    id: str
    title: str
    subject: str
    grade_level: str
    description: str
    units: List[CurriculumUnit]
    total_duration_weeks: int
    created_at: datetime = Field(default_factory=datetime.now)


class StudentProfile(BaseModel):
    """Perfil de estudiante"""
    id: str
    name: str
    grade_level: str
    subjects: List[str]
    learning_style: Optional[str] = None
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    performance_history: Dict[str, Any] = {}


class ChatMessage(BaseModel):
    """Mensaje de chat con agentes"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_type: Optional[AgentType] = None


class AgentRequest(BaseModel):
    """Solicitud a un agente"""
    agent_type: AgentType
    prompt: str
    context: Optional[Dict[str, Any]] = {}
    documents: Optional[List[str]] = []  # IDs de documentos
    parameters: Optional[Dict[str, Any]] = {}


class AgentResponse(BaseModel):
    """Respuesta de un agente"""
    success: bool
    content: str
    data: Optional[Dict[str, Any]] = None
    agent_type: AgentType
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class LessonPlan(BaseModel):
    """Plan de lección"""
    id: str
    title: str
    subject: str
    grade_level: str
    duration_minutes: int
    objectives: List[str]
    materials: List[str]
    activities: List[Dict[str, Any]]
    assessment: str
    homework: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class PerformanceReport(BaseModel):
    """Reporte de rendimiento"""
    id: str
    student_id: str
    subject: str
    grade_level: str
    period: str
    scores: Dict[str, float]
    strengths: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]
    generated_at: datetime = Field(default_factory=datetime.now)


class UnifiedChatRequest(BaseModel):
    """Request para chat unificado"""
    message: str
    selected_agents: List[str]
    chat_mode: str = "individual"
    context: Optional[Dict[str, Any]] = None


class CoachingSession(BaseModel):
    """Modelo para sesiones de coaching"""
    id: str
    student_id: str
    student_name: str
    student_message: str
    coach_response: str
    emotional_state: Optional[str] = "neutral"
    session_metadata: Optional[Dict[str, Any]] = None
    intervention_needed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class StudentStats(BaseModel):
    """Estadísticas del estudiante"""
    student_id: str
    student_name: str
    total_sessions: int = 0
    coaching_sessions: int = 0
    last_activity: Optional[datetime] = None
    emotional_trend: List[str] = []
    intervention_alerts: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
