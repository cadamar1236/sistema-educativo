"""
Módulo de agentes educativos usando Agno
"""

from .base_agent import BaseEducationalAgent
from .exam_generator.agent import ExamGeneratorAgent
from .curriculum_creator.agent import CurriculumCreatorAgent
from .tutor.agent import TutorAgent
from .lesson_planner.agent import LessonPlannerAgent
from .document_analyzer.agent import DocumentAnalyzerAgent

__all__ = [
    "BaseEducationalAgent",
    "ExamGeneratorAgent", 
    "CurriculumCreatorAgent",
    "TutorAgent",
    "LessonPlannerAgent",
    "DocumentAnalyzerAgent"
]
