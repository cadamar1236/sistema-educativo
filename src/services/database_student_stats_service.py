"""
Servicio de estadísticas de estudiantes usando PostgreSQL
Reemplaza el sistema de archivos JSON con base de datos relacional
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from src.auth.users_db import engine, get_session

try:
    from src.models.student_stats_models import (
        StudentStats, StudentActivity, StudentAchievement, 
        StudentSubjectProgress, StudentBadge
    )
except ImportError:
    from models.student_stats_models import (
        StudentStats, StudentActivity, StudentAchievement, 
        StudentSubjectProgress, StudentBadge
    )

class DatabaseStudentStatsService:
    """
    Servicio de estadísticas usando PostgreSQL
    """
    
    def __init__(self):
        self.engine = engine
        # Crear las tablas si no existen
        self._init_tables()
    
    def _init_tables(self):
        """Crear las tablas si no existen"""
        try:
            try:
                from src.models.student_stats_models import Base
            except ImportError:
                from models.student_stats_models import Base
            
            Base.metadata.create_all(bind=self.engine)
            print("✅ Tablas de estadísticas inicializadas")
        except Exception as e:
            print(f"❌ Error inicializando tablas: {e}")
    
    def get_or_create_student_stats(self, student_id: str, email: str = None) -> StudentStats:
        """Obtener o crear estadísticas del estudiante
        
        Busca por email real y formato normalizado para compatibilidad
        """
        with get_session() as session:
            # Primero buscar con el ID directo
            stats = session.query(StudentStats).filter(StudentStats.id == student_id).first()
            
            # Si no se encuentra y es un email, buscar con formato normalizado
            if not stats and "@" in student_id:
                normalized_id = student_id.replace("@", "_at_").replace(".", "_dot_")
                stats = session.query(StudentStats).filter(StudentStats.id == normalized_id).first()
                print(f"🔄 Buscando con formato normalizado: {normalized_id}")
                
                if stats:
                    # Migrar el registro al nuevo formato
                    print(f"🔄 Migrando estadísticas de {normalized_id} a {student_id}")
                    old_stats = stats
                    
                    # Crear nuevo registro con email real
                    stats = StudentStats(
                        id=student_id,
                        email=student_id,
                        total_points=old_stats.total_points,
                        level=old_stats.level,
                        progress_percentage=old_stats.progress_percentage,
                        lessons_completed=old_stats.lessons_completed,
                        exercises_done=old_stats.exercises_done,
                        total_time_spent=old_stats.total_time_spent,
                        current_streak=old_stats.current_streak,
                        longest_streak=old_stats.longest_streak,
                        total_achievements=old_stats.total_achievements
                    )
                    session.add(stats)
                    
                    # Migrar actividades asociadas
                    activities = session.query(StudentActivity).filter(StudentActivity.student_id == normalized_id).all()
                    for activity in activities:
                        activity.student_id = student_id
                    
                    # Eliminar registro normalizado
                    session.delete(old_stats)
                    session.commit()
                    session.refresh(stats)
                    print(f"✅ Migración completada para {student_id}")
            
            if not stats:
                # Crear nuevas estadísticas
                stats = StudentStats(
                    id=student_id,
                    email=email or student_id,
                    total_points=0,
                    level=1,
                    progress_percentage=0.0,
                    lessons_completed=0,
                    exercises_done=0,
                    total_time_spent=0,
                    current_streak=0,
                    longest_streak=0,
                    total_achievements=0
                )
                session.add(stats)
                session.commit()
                session.refresh(stats)
                print(f"✅ Nuevas estadísticas creadas para {student_id}")
            
            return stats
    
    def update_student_activity(self, student_id: str, activity: Dict[str, Any]) -> bool:
        """
        Actualiza la actividad del estudiante en la base de datos
        """
        try:
            with get_session() as session:
                # Registrar la actividad
                    # Usar email real si está disponible en la actividad
                    real_email = activity.get("user_email") or activity.get("email") or student_id
                    activity_record = StudentActivity(
                        id=str(uuid.uuid4()),
                        student_id=real_email,
                        activity_type=activity.get("type", "unknown"),
                        activity_data=activity,
                        endpoint=activity.get("endpoint"),
                        agent_type=activity.get("agent_type"),
                        duration_seconds=activity.get("duration_seconds"),
                        response_status=activity.get("response_status"),
                        date=datetime.now().strftime("%Y-%m-%d"),
                        hour=datetime.now().hour
                    )
                    session.add(activity_record)
                
                    # Actualizar estadísticas del estudiante
                    stats = self.get_or_create_student_stats(real_email, real_email)
                
                    # Incrementar contadores según el tipo de actividad
                    if activity.get("type") in ["agent_interaction", "chat_session"]:
                        stats.exercises_done += 1
                        # Sumar puntos si vienen en la actividad, si no, sumar 5 por defecto
                        stats.total_points += int(activity.get("points_earned", 5))
                
                    # Actualizar tiempo total si está disponible
                    if activity.get("duration_seconds"):
                        stats.total_time_spent += int(activity.get("duration_seconds", 0) / 60)
                
                    # Actualizar timestamp de última actividad
                    stats.last_activity_at = datetime.now()
                    stats.updated_at = datetime.now()
                
                    # Calcular nivel basado en puntos (cada 100 puntos = 1 nivel)
                    stats.level = max(1, stats.total_points // 100 + 1)
                
                    session.add(stats)
                    session.commit()
                
                    print(f"✅ Actividad registrada para {real_email}: {activity.get('type')}")
                    return True
                
        except Exception as e:
            print(f"❌ Error actualizando actividad del estudiante: {e}")
            return False
    
    def get_dashboard_stats(self, student_id: str) -> Dict[str, Any]:
        """
        Obtiene todas las estadísticas necesarias para el dashboard
        """
        try:
            with get_session() as session:
                # Obtener estadísticas básicas
                stats = self.get_or_create_student_stats(student_id)
                
                # Obtener actividades de hoy (buscar en ambos formatos)
                today = datetime.now().strftime("%Y-%m-%d")
                normalized_id = student_id.replace("@", "_at_").replace(".", "_dot_") if "@" in student_id else None
                
                today_activities = session.query(StudentActivity).filter(
                    and_(
                        StudentActivity.student_id.in_([student_id] + ([normalized_id] if normalized_id else [])),
                        StudentActivity.date == today
                    )
                ).all()
                
                # Calcular estadísticas de hoy
                today_lessons = len([a for a in today_activities if a.activity_type == "lesson"])
                today_exercises = len([a for a in today_activities if a.activity_type == "agent_interaction"])
                today_time = sum([a.duration_seconds or 0 for a in today_activities]) / 60
                
                # Obtener actividades recientes (últimos 7 días, buscar en ambos formatos)
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                recent_activities = session.query(StudentActivity).filter(
                    and_(
                        StudentActivity.student_id.in_([student_id] + ([normalized_id] if normalized_id else [])),
                        StudentActivity.date >= week_ago
                    )
                ).order_by(desc(StudentActivity.created_at)).limit(10).all()
                
                # Obtener logros recientes (buscar en ambos formatos)
                recent_achievements = session.query(StudentAchievement).filter(
                    StudentAchievement.student_id.in_([student_id] + ([normalized_id] if normalized_id else []))
                ).order_by(desc(StudentAchievement.earned_at)).limit(5).all()
                
                # Obtener progreso por materia (buscar en ambos formatos)
                subject_progress = session.query(StudentSubjectProgress).filter(
                    StudentSubjectProgress.student_id.in_([student_id] + ([normalized_id] if normalized_id else []))
                ).all()
                
                # Obtener insignias (buscar en ambos formatos)
                badges = session.query(StudentBadge).filter(
                    StudentBadge.student_id.in_([student_id] + ([normalized_id] if normalized_id else []))
                ).all()
                
                # Construir respuesta
                return {
                    "student": {
                        "name": stats.name or "Usuario",
                        "email": stats.email,
                        "id": stats.id,
                        "total_points": stats.total_points,
                        "level": stats.level,
                        "progress_percentage": stats.progress_percentage,
                        "today_activity": {
                            "lessons_completed": today_lessons,
                            "exercises_done": today_exercises,
                            "time_spent": int(today_time)
                        },
                        "upcoming_classes": [
                            {"subject": "Matemáticas", "time": "14:30", "teacher": "Prof. García"},
                            {"subject": "Física", "time": "16:00", "teacher": "Prof. López"}
                        ],
                        "recent_achievements": [
                            {
                                "name": a.title,
                                "icon": a.icon or "🏆",
                                "date": a.earned_at.strftime("%Y-%m-%d")
                            } for a in recent_achievements
                        ],
                        "badges": [
                            {
                                "name": b.badge_name,
                                "icon": b.icon or "🏅",
                                "level": b.level
                            } for b in badges
                        ],
                        "subject_stats": [
                            {
                                "subject": sp.subject,
                                "progress": sp.progress_percentage,
                                "points": sp.points,
                                "grade": sp.grade
                            } for sp in subject_progress
                        ],
                        "trends": self._calculate_trends(student_id, session)
                    },
                    "system_status": {
                        "server_status": "online",
                        "last_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "active_users": self._get_active_users_count(session)
                    },
                    "recommendations": self._get_personalized_recommendations(stats)
                }
                
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas del dashboard: {e}")
            # Fallback a datos mock si hay error
            return self._get_mock_dashboard_stats(student_id)
    
    def _calculate_trends(self, student_id: str, session: Session) -> Dict[str, List]:
        """Calcular tendencias de los últimos 7 días"""
        try:
            # Obtener actividades de los últimos 7 días agrupadas por día
            week_ago = datetime.now() - timedelta(days=7)
            
            daily_stats = session.query(
                StudentActivity.date,
                func.count(StudentActivity.id).label('activity_count'),
                func.sum(
                    func.case(
                        (StudentActivity.activity_type == 'agent_interaction', 5),
                        else_=0
                    )
                ).label('points')
            ).filter(
                and_(
                    StudentActivity.student_id == student_id,
                    StudentActivity.created_at >= week_ago
                )
            ).group_by(StudentActivity.date).all()
            
            # Crear listas de tendencias
            points_trend = []
            activity_trend = []
            
            for i in range(7):
                date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
                day_stats = next((s for s in daily_stats if s.date == date), None)
                
                if day_stats:
                    points_trend.append(day_stats.points or 0)
                    activity_trend.append(day_stats.activity_count or 0)
                else:
                    points_trend.append(0)
                    activity_trend.append(0)
            
            return {
                "points_trend": points_trend,
                "activity_trend": activity_trend
            }
            
        except Exception as e:
            print(f"Error calculando tendencias: {e}")
            return {
                "points_trend": [0, 5, 10, 8, 12, 15, 18],
                "activity_trend": [0, 2, 4, 3, 5, 6, 7]
            }
    
    def _get_active_users_count(self, session: Session) -> int:
        """Obtener número de usuarios activos hoy"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            count = session.query(
                func.count(func.distinct(StudentActivity.student_id))
            ).filter(StudentActivity.date == today).scalar()
            
            return count or 0
        except:
            return 1
    
    def _get_personalized_recommendations(self, stats: StudentStats) -> List[Dict[str, str]]:
        """Generar recomendaciones personalizadas"""
        recommendations = []
        
        # Basado en el nivel
        if stats.level < 3:
            recommendations.append({
                "type": "study",
                "message": "Completa más ejercicios para subir de nivel",
                "priority": "high"
            })
        
        # Basado en la actividad
        if stats.exercises_done < 10:
            recommendations.append({
                "type": "practice",
                "message": "Prueba interactuar con más agentes educativos",
                "priority": "medium"
            })
        
        # Basado en el tiempo
        time_hours = stats.total_time_spent / 60
        if time_hours < 5:
            recommendations.append({
                "type": "engagement",
                "message": "Dedica más tiempo al estudio para mejores resultados",
                "priority": "low"
            })
        
        return recommendations or [
            {
                "type": "general",
                "message": "¡Sigue así! Estás progresando muy bien",
                "priority": "info"
            }
        ]
    
    def _get_mock_dashboard_stats(self, student_id: str) -> Dict[str, Any]:
        """Estadísticas mock como fallback"""
        return {
            "student": {
                "name": "Usuario",
                "email": student_id,
                "id": student_id,
                "total_points": 0,
                "level": 1,
                "progress_percentage": 0,
                "today_activity": {
                    "lessons_completed": 0,
                    "exercises_done": 0,
                    "time_spent": 0
                },
                "upcoming_classes": [],
                "recent_achievements": [],
                "badges": [],
                "subject_stats": [],
                "trends": {
                    "points_trend": [0, 0, 0, 0, 0, 0, 0],
                    "activity_trend": [0, 0, 0, 0, 0, 0, 0]
                }
            },
            "system_status": {
                "server_status": "online",
                "last_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "active_users": 1
            },
            "recommendations": [
                {
                    "type": "welcome",
                    "message": "¡Bienvenido! Comienza interactuando con los agentes",
                    "priority": "info"
                }
            ]
        }
    
    def create_achievement(self, student_id: str, achievement_type: str, title: str, points: int = 10):
        """Crear un nuevo logro para el estudiante"""
        try:
            with get_session() as session:
                achievement = StudentAchievement(
                    id=str(uuid.uuid4()),
                    student_id=student_id,
                    achievement_type=achievement_type,
                    title=title,
                    points_awarded=points
                )
                session.add(achievement)
                
                # Actualizar puntos del estudiante
                stats = session.query(StudentStats).filter(StudentStats.id == student_id).first()
                if stats:
                    stats.total_points += points
                    stats.total_achievements += 1
                    stats.level = max(1, stats.total_points // 100 + 1)
                    session.add(stats)
                
                session.commit()
                print(f"✅ Logro creado para {student_id}: {title}")
                return True
                
        except Exception as e:
            print(f"❌ Error creando logro: {e}")
            return False
