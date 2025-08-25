"""
Script para crear las tablas de estadísticas de estudiantes en PostgreSQL
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

# Crear el engine
engine = create_engine(DATABASE_URL, echo=True)

# SQL para crear las tablas
CREATE_TABLES_SQL = """
-- Tabla para estadísticas básicas de estudiantes
CREATE TABLE IF NOT EXISTS student_stats (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(255) NOT NULL,
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    progress_percentage FLOAT DEFAULT 0.0,
    study_streak_current INTEGER DEFAULT 0,
    study_streak_longest INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id)
);

-- Tabla para actividades de estudiantes
CREATE TABLE IF NOT EXISTS student_activities (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date DATE DEFAULT CURRENT_DATE,
    duration_seconds FLOAT DEFAULT 0.0,
    points_earned INTEGER DEFAULT 0
);

-- Tabla para logros/badges de estudiantes
CREATE TABLE IF NOT EXISTS student_achievements (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(255) NOT NULL,
    achievement_name VARCHAR(255) NOT NULL,
    achievement_type VARCHAR(100) NOT NULL,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    achievement_data JSONB DEFAULT '{}'
);

-- Tabla para progreso por materias
CREATE TABLE IF NOT EXISTS student_subject_progress (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(255) NOT NULL,
    subject_name VARCHAR(255) NOT NULL,
    progress_percentage FLOAT DEFAULT 0.0,
    points_earned INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, subject_name)
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_student_stats_student_id ON student_stats(student_id);
CREATE INDEX IF NOT EXISTS idx_student_activities_student_id ON student_activities(student_id);
CREATE INDEX IF NOT EXISTS idx_student_activities_date ON student_activities(date);
CREATE INDEX IF NOT EXISTS idx_student_activities_type ON student_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_student_achievements_student_id ON student_achievements(student_id);
CREATE INDEX IF NOT EXISTS idx_student_subject_progress_student_id ON student_subject_progress(student_id);

-- Función para actualizar el timestamp de updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar automáticamente updated_at en student_stats
DROP TRIGGER IF EXISTS update_student_stats_updated_at ON student_stats;
CREATE TRIGGER update_student_stats_updated_at 
    BEFORE UPDATE ON student_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
"""

def create_stats_tables():
    """Crear las tablas de estadísticas de estudiantes"""
    try:
        print("🔄 Conectando a la base de datos...")
        with engine.connect() as connection:
            print("✅ Conexión establecida")
            
            # Ejecutar el SQL
            print("🔄 Creando tablas...")
            connection.execute(text(CREATE_TABLES_SQL))
            connection.commit()
            print("✅ Tablas creadas exitosamente")
            
            # Verificar que las tablas existen
            print("🔄 Verificando tablas...")
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'student_%'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            print("✅ Tablas encontradas:")
            for table in tables:
                print(f"  - {table}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Creando tablas de estadísticas de estudiantes...")
    success = create_stats_tables()
    if success:
        print("✅ ¡Proceso completado exitosamente!")
    else:
        print("❌ El proceso falló. Revisa los errores arriba.")
