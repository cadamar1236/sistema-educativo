import asyncio
import logging
import asyncpg
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, primary_url: str, replica_url: str, pool_size: int = 20):
        self.primary_url = primary_url
        self.replica_url = replica_url
        self.pool_size = pool_size
        self.primary_pool = None
        self.replica_pool = None

    async def initialize_pools(self):
        """Inicializar los pools de conexiones"""
        try:
            # Pool para escritura (maestro)
            self.primary_pool = await asyncpg.create_pool(
                self.primary_url,
                min_size=5,
                max_size=self.pool_size,
                command_timeout=60
            )
            
            # Pool para lectura (réplica)
            self.replica_pool = await asyncpg.create_pool(
                self.replica_url,
                min_size=5,
                max_size=self.pool_size,
                command_timeout=60
            )
            
            logger.info("Pools de conexión inicializados exitosamente")
        except Exception as e:
            logger.error(f"Error al inicializar pools: {e}")
            raise

    async def close_pools(self):
        """Cerrar todos los pools de conexiones"""
        if self.primary_pool:
            await self.primary_pool.close()
        if self.replica_pool:
            await self.replica_pool.close()
        logger.info("Pools de conexión cerrados")

    @asynccontextmanager
    async def acquire_primary(self):
        """Obtener conexión del pool principal (escritura)"""
        async with self.primary_pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def acquire_replica(self):
        """Obtener conexión del pool de réplica (lectura)"""
        async with self.replica_pool.acquire() as conn:
            yield conn

    async def execute_write(self, query: str, *args) -> Any:
        """Ejecutar consulta de escritura en la base de datos principal"""
        async with self.acquire_primary() as conn:
            try:
                result = await conn.execute(query, *args)
                return result
            except Exception as e:
                logger.error(f"Error en escritura: {e}")
                raise

    async def execute_read(self, query: str, *args) -> List[Dict[str, Any]]:
        """Ejecutar consulta de lectura en la réplica"""
        async with self.acquire_replica() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error en lectura: {e}")
                raise

    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """Ejecutar múltiples consultas en una transacción"""
        async with self.acquire_primary() as conn:
            async with conn.transaction():
                try:
                    for query, params in queries:
                        await conn.execute(query, *params)
                    return True
                except Exception as e:
                    logger.error(f"Error en transacción: {e}")
                    return False

    async def get_replication_status(self) -> Dict[str, Any]:
        """Obtener el estado actual de la replicación"""
        query = """
        SELECT 
            client_addr,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            write_lag,
            flush_lag,
            replay_lag
        FROM pg_stat_replication
        """
        return await self.execute_read(query)

    async def get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        query = """
        SELECT 
            datname,
            numbackends,
            xact_commit,
            xact_rollback,
            blks_read,
            blks_hit,
            tup_returned,
            tup_fetched,
            tup_inserted,
            tup_updated,
            tup_deleted
        FROM pg_stat_database
        WHERE datname = 'educational_system'
        """
        result = await self.execute_read(query)
        return result[0] if result else {}

    async def optimize_queries(self):
        """Ejecutar optimización de consultas"""
        queries = [
            "ANALYZE student_activities",
            "ANALYZE users",
            "ANALYZE agents",
            "VACUUM ANALYZE student_activities"
        ]
        
        async with self.acquire_primary() as conn:
            for query in queries:
                await conn.execute(query)
        logger.info("Optimización de consultas completada")

# Pool de conexiones con patrón singleton
db_manager = None

async def get_database_manager() -> DatabaseManager:
    """Obtener el gestor de base de datos global"""
    global db_manager
    if db_manager is None:
        from src.config import settings
        db_manager = DatabaseManager(
            primary_url=settings.database_url,
            replica_url=settings.replica_database_url,
            pool_size=20
        )
        await db_manager.initialize_pools()
    return db_manager

# Decorador para manejo de conexiones
async def with_database(func):
    """Decorador para manejar conexiones de base de datos"""
    async def wrapper(*args, **kwargs):
        db = await get_database_manager()
        return await func(db, *args, **kwargs)
    return wrapper

# Ejemplo de uso con monitoreo de rendimiento
class DatabaseMonitor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def monitor_query_performance(self, query: str, *args) -> Dict[str, Any]:
        """Monitorear el rendimiento de una consulta"""
        start_time = time.time()
        
        try:
            result = await self.db_manager.execute_read(query, *args)
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "execution_time": execution_time,
                "rows_affected": len(result),
                "query": query
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "query": query
            }

    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del pool de conexiones"""
        if not self.db_manager.primary_pool:
            return {}
        
        primary_stats = self.db_manager.primary_pool.get_status()
        replica_stats = self.db_manager.replica_pool.get_status()
        
        return {
            "primary_pool": {
                "size": primary_stats["size"],
                "available": primary_stats["available"],
                "used": primary_stats["size"] - primary_stats["available"]
            },
            "replica_pool": {
                "size": replica_stats["size"],
                "available": replica_stats["available"],
                "used": replica_stats["size"] - replica_stats["available"]
            }
        }