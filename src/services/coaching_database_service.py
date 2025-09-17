"""
Servicio de base de datos para sesiones de coaching
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncpg
import json
import uuid

logger = logging.getLogger(__name__)

class CoachingDatabaseService:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def initialize(self):
        """Inicializar conexión a la base de datos"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Crear tablas si no existen
            await self.create_tables()
            logger.info("Servicio de coaching database inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando coaching database: {e}")
            raise

    async def create_tables(self):
        """Crear las tablas necesarias para coaching"""
        async with self.pool.acquire() as conn:
            # Tabla para sesiones de coaching
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS coaching_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id VARCHAR(255) NOT NULL,
                    student_name VARCHAR(255) NOT NULL,
                    student_message TEXT NOT NULL,
                    coach_response TEXT NOT NULL,
                    emotional_state VARCHAR(50) DEFAULT 'neutral',
                    session_metadata JSONB DEFAULT '{}',
                    intervention_needed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Tabla para estadísticas de estudiantes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS student_stats (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id VARCHAR(255) UNIQUE NOT NULL,
                    student_name VARCHAR(255) NOT NULL,
                    total_sessions INTEGER DEFAULT 0,
                    coaching_sessions INTEGER DEFAULT 0,
                    last_activity TIMESTAMP WITH TIME ZONE,
                    emotional_trend JSONB DEFAULT '[]',
                    intervention_alerts INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Índices para mejorar rendimiento
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_coaching_sessions_student_id 
                ON coaching_sessions(student_id);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_coaching_sessions_created_at 
                ON coaching_sessions(created_at);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_student_stats_student_id 
                ON student_stats(student_id);
            """)

            logger.info("Tablas de coaching creadas/verificadas correctamente")

    async def save_coaching_session(self, session_data: Dict[str, Any]) -> str:
        """Guardar una sesión de coaching"""
        try:
            async with self.pool.acquire() as conn:
                session_id = str(uuid.uuid4())
                
                await conn.execute("""
                    INSERT INTO coaching_sessions 
                    (id, student_id, student_name, student_message, coach_response, 
                     emotional_state, session_metadata, intervention_needed)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    session_id,
                    session_data.get('student_id', 'unknown'),
                    session_data.get('student_name', 'Unknown'),
                    session_data.get('student_message', ''),
                    session_data.get('coach_response', ''),
                    session_data.get('emotional_state', 'neutral'),
                    json.dumps(session_data.get('metadata', {})),
                    session_data.get('intervention_needed', False)
                )
                
                # Actualizar estadísticas del estudiante
                await self.update_student_stats(
                    session_data.get('student_id', 'unknown'),
                    session_data.get('student_name', 'Unknown'),
                    session_data.get('emotional_state', 'neutral')
                )
                
                logger.info(f"Sesión de coaching guardada: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Error guardando sesión de coaching: {e}")
            raise

    async def update_student_stats(self, student_id: str, student_name: str, emotional_state: str):
        """Actualizar estadísticas del estudiante"""
        try:
            async with self.pool.acquire() as conn:
                # Verificar si el estudiante existe
                existing = await conn.fetchrow(
                    "SELECT * FROM student_stats WHERE student_id = $1", 
                    student_id
                )
                
                if existing:
                    # Actualizar estadísticas existentes
                    emotional_trend = json.loads(existing['emotional_trend'] or '[]')
                    emotional_trend.append(emotional_state)
                    
                    # Mantener solo los últimos 20 estados emocionales
                    if len(emotional_trend) > 20:
                        emotional_trend = emotional_trend[-20:]
                    
                    await conn.execute("""
                        UPDATE student_stats 
                        SET total_sessions = total_sessions + 1,
                            coaching_sessions = coaching_sessions + 1,
                            last_activity = NOW(),
                            emotional_trend = $1,
                            updated_at = NOW()
                        WHERE student_id = $2
                    """, 
                        json.dumps(emotional_trend),
                        student_id
                    )
                else:
                    # Crear nuevas estadísticas
                    await conn.execute("""
                        INSERT INTO student_stats 
                        (student_id, student_name, total_sessions, coaching_sessions, 
                         last_activity, emotional_trend)
                        VALUES ($1, $2, 1, 1, NOW(), $3)
                    """, 
                        student_id,
                        student_name,
                        json.dumps([emotional_state])
                    )
                
                logger.info(f"Estadísticas actualizadas para estudiante: {student_id}")
                
        except Exception as e:
            logger.error(f"Error actualizando estadísticas del estudiante: {e}")
            raise

    async def get_student_coaching_history(self, student_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de coaching de un estudiante"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM coaching_sessions 
                    WHERE student_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, student_id, limit)
                
                sessions = []
                for row in rows:
                    sessions.append({
                        'id': str(row['id']),
                        'student_message': row['student_message'],
                        'coach_response': row['coach_response'],
                        'emotional_state': row['emotional_state'],
                        'intervention_needed': row['intervention_needed'],
                        'created_at': row['created_at'].isoformat(),
                        'metadata': json.loads(row['session_metadata'] or '{}')
                    })
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error obteniendo historial de coaching: {e}")
            return []

    async def get_student_stats(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de un estudiante"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM student_stats WHERE student_id = $1", 
                    student_id
                )
                
                if row:
                    return {
                        'student_id': row['student_id'],
                        'student_name': row['student_name'],
                        'total_sessions': row['total_sessions'],
                        'coaching_sessions': row['coaching_sessions'],
                        'last_activity': row['last_activity'].isoformat() if row['last_activity'] else None,
                        'emotional_trend': json.loads(row['emotional_trend'] or '[]'),
                        'intervention_alerts': row['intervention_alerts'],
                        'created_at': row['created_at'].isoformat(),
                        'updated_at': row['updated_at'].isoformat()
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del estudiante: {e}")
            return None

    async def get_coaching_analytics(self) -> Dict[str, Any]:
        """Obtener analytics generales de coaching"""
        try:
            async with self.pool.acquire() as conn:
                # Total de sesiones
                total_sessions = await conn.fetchval(
                    "SELECT COUNT(*) FROM coaching_sessions"
                )
                
                # Sesiones en las últimas 24 horas
                recent_sessions = await conn.fetchval("""
                    SELECT COUNT(*) FROM coaching_sessions 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                # Estudiantes únicos
                unique_students = await conn.fetchval(
                    "SELECT COUNT(DISTINCT student_id) FROM coaching_sessions"
                )
                
                # Estudiantes que necesitan intervención
                interventions_needed = await conn.fetchval("""
                    SELECT COUNT(DISTINCT student_id) FROM coaching_sessions 
                    WHERE intervention_needed = TRUE 
                    AND created_at >= NOW() - INTERVAL '7 days'
                """)
                
                return {
                    'total_sessions': total_sessions or 0,
                    'recent_sessions_24h': recent_sessions or 0,
                    'unique_students': unique_students or 0,
                    'interventions_needed': interventions_needed or 0,
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo analytics: {e}")
            return {
                'total_sessions': 0,
                'recent_sessions_24h': 0,
                'unique_students': 0,
                'interventions_needed': 0,
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }

    async def close(self):
        """Cerrar conexiones a la base de datos"""
        if self.pool:
            await self.pool.close()
            logger.info("Conexiones de coaching database cerradas")

# Instancia global del servicio
coaching_db_service = None

async def get_coaching_db_service() -> CoachingDatabaseService:
    """Obtener instancia del servicio de coaching database"""
    global coaching_db_service
    if coaching_db_service is None:
        # Esta URL debería venir de las variables de entorno
        DATABASE_URL = "postgresql+psycopg://eduadmin:c1d2Papa1236.,@julialabs.postgres.database.azure.com:5432/sistema_educativo?sslmode=require"
        # Convertir formato para asyncpg
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
        
        coaching_db_service = CoachingDatabaseService(DATABASE_URL)
        await coaching_db_service.initialize()
    
    return coaching_db_service
