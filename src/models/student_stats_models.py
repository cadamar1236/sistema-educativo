"""
Modelos de base de datos para estadísticas de estudiantes
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Dict, Any, List

# Usar la misma base que users_db
from src.auth.users_db import Base

class StudentStats(Base):
    """Estadísticas generales del estudiante"""
    __tablename__ = "student_stats"
    
    id = Column(String, primary_key=True, index=True)  # email normalizado como ID
    email = Column(String, index=True, nullable=False)  # email original
    name = Column(String, nullable=True)
    
    # Estadísticas básicas
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    progress_percentage = Column(Float, default=0.0)
    
    # Contadores de actividad
    lessons_completed = Column(Integer, default=0)
    exercises_done = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)  # en minutos
    
    # Racha y logros
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_achievements = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)


class StudentActivity(Base):
    """Registro de actividades del estudiante"""
    __tablename__ = "student_activities"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    student_id = Column(String, index=True, nullable=False)  # FK a student_stats
    
    # Detalles de la actividad
    activity_type = Column(String, nullable=False)  # agent_interaction, lesson, exercise, etc.
    activity_data = Column(JSON, nullable=True)  # datos específicos de la actividad
    
    # Contexto
    endpoint = Column(String, nullable=True)
    agent_type = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    response_status = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    date = Column(String, index=True, nullable=False)  # YYYY-MM-DD para consultas rápidas
    hour = Column(Integer, nullable=True)  # 0-23 para análisis por hora


class StudentAchievement(Base):
    """Logros del estudiante"""
    __tablename__ = "student_achievements"
    
    id = Column(String, primary_key=True)  # UUID
    student_id = Column(String, index=True, nullable=False)
    
    # Detalles del logro
    achievement_type = Column(String, nullable=False)  # streak, points, completion, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    points_awarded = Column(Integer, default=0)
    
    # Timestamp
    earned_at = Column(DateTime, default=datetime.utcnow, index=True)


class StudentSubjectProgress(Base):
    """Progreso por materia"""
    __tablename__ = "student_subject_progress"
    
    id = Column(String, primary_key=True)
    student_id = Column(String, index=True, nullable=False)
    
    # Materia
    subject = Column(String, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    grade = Column(String, nullable=True)  # A, B, C, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StudentBadge(Base):
    """Insignias del estudiante"""
    __tablename__ = "student_badges"
    
    id = Column(String, primary_key=True)
    student_id = Column(String, index=True, nullable=False)
    
    # Detalles de la insignia
    badge_name = Column(String, nullable=False)
    badge_type = Column(String, nullable=False)  # subject, activity, achievement
    icon = Column(String, nullable=True)
    level = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    
    # Timestamp
    earned_at = Column(DateTime, default=datetime.utcnow)
