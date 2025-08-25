"""
Modelos SQLAlchemy para estadísticas de estudiantes
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from src.auth.users_db import Base

class StudentStats(Base):
    """Estadísticas básicas del estudiante"""
    __tablename__ = 'student_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), nullable=False, unique=True, index=True)
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    progress_percentage = Column(Float, default=0.0)
    study_streak_current = Column(Integer, default=0)
    study_streak_longest = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StudentActivity(Base):
    """Actividades del estudiante"""
    __tablename__ = 'student_activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    activity_data = Column(JSONB, nullable=False, default={})
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    date = Column(Date, default=datetime.utcnow().date, index=True)
    duration_seconds = Column(Float, default=0.0)
    points_earned = Column(Integer, default=0)

class StudentAchievement(Base):
    """Logros y badges del estudiante"""
    __tablename__ = 'student_achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), nullable=False, index=True)
    achievement_name = Column(String(255), nullable=False)
    achievement_type = Column(String(100), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    achievement_data = Column(JSONB, default={})

class StudentSubjectProgress(Base):
    """Progreso del estudiante por materia"""
    __tablename__ = 'student_subject_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), nullable=False)
    subject_name = Column(String(255), nullable=False)
    progress_percentage = Column(Float, default=0.0)
    points_earned = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_name', name='uq_student_subject'),
        Index('idx_student_subject_progress_student_id', 'student_id'),
    )

class StudentBadge(Base):
    """Badges/insignias del estudiante"""
    __tablename__ = 'student_badges'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), nullable=False, index=True)
    badge_name = Column(String(255), nullable=False)
    badge_level = Column(Integer, default=1)
    earned_at = Column(DateTime, default=datetime.utcnow)
    badge_data = Column(JSONB, default={})
