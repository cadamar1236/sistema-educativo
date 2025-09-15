#!/usr/bin/env python3
"""
Script para migrar student_ids normalizados a emails reales en la base de datos
"""

import sys
import os
import re

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.auth.users_db import get_session
    from src.models.student_stats_models import StudentStats, StudentActivity, StudentAchievement, StudentBadge, StudentSubjectProgress
except ImportError:
    from auth.users_db import get_session
    from models.student_stats_models import StudentStats, StudentActivity, StudentAchievement, StudentBadge, StudentSubjectProgress

def denormalize_email(normalized_id: str) -> str:
    """Convierte un ID normalizado de vuelta a un email"""
    if "_at_" in normalized_id and "_dot_" in normalized_id:
        # Es un email normalizado, convertirlo de vuelta
        email = normalized_id.replace("_at_", "@").replace("_dot_", ".")
        return email
    return normalized_id

def migrate_student_data():
    """Migra todos los datos de estudiantes con IDs normalizados a emails reales"""
    
    print("🔄 Iniciando migración de student_ids normalizados...")
    
    with get_session() as session:
        # 1. Migrar StudentStats
        print("📊 Migrando StudentStats...")
        stats_records = session.query(StudentStats).all()
        
        for stats in stats_records:
            old_id = stats.id
            new_id = denormalize_email(old_id)
            
            if old_id != new_id:  # Solo si cambió
                print(f"  📧 Migrando {old_id} → {new_id}")
                
                # Verificar si ya existe un registro con el nuevo ID
                existing = session.query(StudentStats).filter(StudentStats.id == new_id).first()
                if existing:
                    print(f"  ⚠️  Ya existe registro para {new_id}, consolidando datos...")
                    # Consolidar datos (tomar el máximo de cada campo)
                    existing.total_points = max(existing.total_points, stats.total_points)
                    existing.level = max(existing.level, stats.level)
                    existing.exercises_done = max(existing.exercises_done, stats.exercises_done)
                    existing.total_time_spent = max(existing.total_time_spent, stats.total_time_spent)
                    existing.email = new_id  # Asegurar que el email esté correcto
                    
                    # Eliminar el registro duplicado
                    session.delete(stats)
                else:
                    # Simplemente actualizar el ID
                    stats.id = new_id
                    stats.email = new_id
        
        # 2. Migrar StudentActivity
        print("📝 Migrando StudentActivity...")
        activity_records = session.query(StudentActivity).all()
        
        for activity in activity_records:
            old_student_id = activity.student_id
            new_student_id = denormalize_email(old_student_id)
            
            if old_student_id != new_student_id:
                print(f"  📧 Migrando actividad {old_student_id} → {new_student_id}")
                activity.student_id = new_student_id
        
        # 3. Migrar StudentAchievement
        print("🏆 Migrando StudentAchievement...")
        achievement_records = session.query(StudentAchievement).all()
        
        for achievement in achievement_records:
            old_student_id = achievement.student_id
            new_student_id = denormalize_email(old_student_id)
            
            if old_student_id != new_student_id:
                print(f"  📧 Migrando logro {old_student_id} → {new_student_id}")
                achievement.student_id = new_student_id
        
        # 4. Migrar StudentBadge
        print("🎖️ Migrando StudentBadge...")
        badge_records = session.query(StudentBadge).all()
        
        for badge in badge_records:
            old_student_id = badge.student_id
            new_student_id = denormalize_email(old_student_id)
            
            if old_student_id != new_student_id:
                print(f"  📧 Migrando insignia {old_student_id} → {new_student_id}")
                badge.student_id = new_student_id
        
        # 5. Migrar StudentSubjectProgress
        print("📈 Migrando StudentSubjectProgress...")
        progress_records = session.query(StudentSubjectProgress).all()
        
        for progress in progress_records:
            old_student_id = progress.student_id
            new_student_id = denormalize_email(old_student_id)
            
            if old_student_id != new_student_id:
                print(f"  📧 Migrando progreso {old_student_id} → {new_student_id}")
                progress.student_id = new_student_id
        
        # Commit todos los cambios
        session.commit()
        print("✅ Migración completada exitosamente!")

def verify_migration():
    """Verifica que la migración se haya realizado correctamente"""
    print("\n🔍 Verificando migración...")
    
    with get_session() as session:
        # Buscar registros que aún tengan formato normalizado
        stats_with_old_format = session.query(StudentStats).filter(
            StudentStats.id.like('%_at_%')
        ).all()
        
        if stats_with_old_format:
            print(f"⚠️  Todavía hay {len(stats_with_old_format)} registros con formato normalizado:")
            for stats in stats_with_old_format:
                print(f"  - {stats.id}")
        else:
            print("✅ Todos los StudentStats han sido migrados!")
        
        # Verificar actividades
        activities_with_old_format = session.query(StudentActivity).filter(
            StudentActivity.student_id.like('%_at_%')
        ).all()
        
        if activities_with_old_format:
            print(f"⚠️  Todavía hay {len(activities_with_old_format)} actividades con formato normalizado")
        else:
            print("✅ Todas las actividades han sido migradas!")

if __name__ == "__main__":
    try:
        migrate_student_data()
        verify_migration()
        print("\n🎉 Migración completa! Ahora las estadísticas deberían funcionar correctamente.")
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()