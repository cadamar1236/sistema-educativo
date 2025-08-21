import asyncio
import json
import logging
from typing import Dict, Any, Optional
import redis.asyncio as redis
from datetime import timedelta
import hashlib
from functools import wraps
import time

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client = None
        self.is_connected = False

    async def connect(self):
        """Establecer conexión con Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Conectado a Redis exitosamente")
        except Exception as e:
            logger.error(f"Error al conectar a Redis: {e}")
            self.is_connected = False

    async def disconnect(self):
        """Cerrar conexión con Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False

    async def get(self, key: str) -> Optional[str]:
        """Obtener valor del caché"""
        if not self.is_connected:
            return None
        try:
            value = await self.redis_client.get(key)
            return value
        except Exception as e:
            logger.error(f"Error al obtener del caché: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Almacenar valor en el caché"""
        if not self.is_connected:
            return False
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error al almacenar en caché: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Eliminar una clave del caché"""
        if not self.is_connected:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar del caché: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Verificar si existe una clave en el caché"""
        if not self.is_connected:
            return False
        try:
            exists = await self.redis_client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Error al verificar existencia en caché: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementar un contador en el caché"""
        if not self.is_connected:
            return None
        try:
            result = await self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Error al incrementar en caché: {e}")
            return None

    async def keys(self, pattern: str = "*") -> list:
        """Obtener todas las claves que coincidan con el patrón"""
        if not self.is_connected:
            return []
        try:
            keys = await self.redis_client.keys(pattern)
            return keys
        except Exception as e:
            logger.error(f"Error al obtener claves del caché: {e}")
            return []

    def generate_cache_key(self, prefix: str, *args) -> str:
        """Generar una clave única para el caché"""
        combined = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(combined.encode()).hexdigest()

# Decorador para caché de funciones
class cache_async:
    def __init__(self, cache_manager: CacheManager, ttl: int = 3600):
        self.cache_manager = cache_manager
        self.ttl = ttl

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave única basada en el nombre de la función y argumentos
            key_parts = [func.__name__] + list(args) + list(kwargs.items())
            key = self.cache_manager.generate_cache_key("cache", *key_parts)
            
            # Intentar obtener del caché
            cached = await self.cache_manager.get(key)
            if cached:
                logger.info(f"Cache hit para {func.__name__}")
                return json.loads(cached)
            
            # Ejecutar la función y almacenar en caché
            result = await func(*args, **kwargs)
            await self.cache_manager.set(key, result, self.ttl)
            logger.info(f"Cache miss para {func.__name__}, almacenado en caché")
            
            return result
        return wrapper

# Estrategias de caché específicas para la aplicación educativa
class EducationalCache:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def cache_student_stats(self, student_id: str, stats: Dict[str, Any]):
        """Cachear estadísticas del estudiante"""
        key = f"student:stats:{student_id}"
        await self.cache.set(key, stats, ttl=1800)  # 30 minutos

    async def get_student_stats(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas del estudiante desde caché"""
        key = f"student:stats:{student_id}"
        data = await self.cache.get(key)
        return json.loads(data) if data else None

    async def cache_dashboard_data(self, student_id: str, data: Dict[str, Any]):
        """Cachear datos del dashboard"""
        key = f"dashboard:{student_id}"
        await self.cache.set(key, data, ttl=900)  # 15 minutos

    async def get_dashboard_data(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Obtener datos del dashboard desde caché"""
        key = f"dashboard:{student_id}"
        data = await self.cache.get(key)
        return json.loads(data) if data else None

    async def cache_agent_response(self, agent_id: str, message: str, response: str):
        """Cachear respuesta de agente"""
        key = f"agent:{agent_id}:{hashlib.md5(message.encode()).hexdigest()}"
        await self.cache.set(key, response, ttl=7200)  # 2 horas

    async def get_agent_response(self, agent_id: str, message: str) -> Optional[str]:
        """Obtener respuesta de agente desde caché"""
        key = f"agent:{agent_id}:{hashlib.md5(message.encode()).hexdigest()}"
        return await self.cache.get(key)

    async def invalidate_student_cache(self, student_id: str):
        """Invalidar caché relacionado con un estudiante"""
        patterns = [
            f"student:stats:{student_id}",
            f"dashboard:{student_id}",
            f"student:activities:{student_id}:*"
        ]
        
        for pattern in patterns:
            keys = await self.cache.keys(pattern)
            for key in keys:
                await self.cache.delete(key)

    async def cache_system_metrics(self, metrics: Dict[str, Any]):
        """Cachear métricas del sistema"""
        key = "system:metrics"
        await self.cache.set(key, metrics, ttl=60)  # 1 minuto

    async def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Obtener métricas del sistema desde caché"""
        key = "system:metrics"
        data = await self.cache.get(key)
        return json.loads(data) if data else None

# Ejemplo de uso con rate limiting
class RateLimiter:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def is_allowed(self, identifier: str, limit: int = 100, window: int = 3600) -> bool:
        """Verificar si una petición está dentro del límite"""
        key = f"rate_limit:{identifier}"
        current = await self.cache.increment(key)
        
        if current == 1:
            # Primera petición en esta ventana
            await self.cache.redis_client.expire(key, window)
        
        return current <= limit

    async def remaining_requests(self, identifier: str, limit: int = 100) -> int:
        """Obtener cuántas peticiones restantes tiene el usuario"""
        key = f"rate_limit:{identifier}"
        current = await self.cache.get(key)
        current = int(current) if current else 0
        return max(0, limit - current)

# Singleton para el gestor de caché global
cache_manager = CacheManager()
educational_cache = EducationalCache(cache_manager)
rate_limiter = RateLimiter(cache_manager)

async def initialize_cache():
    """Inicializar el sistema de caché"""
    await cache_manager.connect()

async def close_cache():
    """Cerrar el sistema de caché"""
    await cache_manager.disconnect()