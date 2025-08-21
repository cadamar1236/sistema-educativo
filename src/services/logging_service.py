import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any
import os
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler

class StructuredLogger:
    """Logger estructurado con formato JSON para microservicios"""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Formato JSON
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler con rotación
        logs_dir = os.path.join(os.path.dirname(__file__), '../../logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, f'{name}.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log_request(self, request_id: str, method: str, path: str, status: int, duration: float, **kwargs):
        """Log para requests HTTP"""
        self.logger.info("HTTP Request", extra={
            'request_id': request_id,
            'method': method,
            'path': path,
            'status': status,
            'duration': duration,
            **kwargs
        })

    def log_database_query(self, query_id: str, query: str, duration: float, **kwargs):
        """Log para queries de base de datos"""
        self.logger.info("Database Query", extra={
            'query_id': query_id,
            'query': query[:200],  # Truncate long queries
            'duration': duration,
            **kwargs
        })

    def log_cache_operation(self, operation: str, key: str, hit: bool, duration: float, **kwargs):
        """Log para operaciones de caché"""
        self.logger.info("Cache Operation", extra={
            'operation': operation,
            'key': key,
            'hit': hit,
            'duration': duration,
            **kwargs
        })

    def log_agent_processing(self, agent_id: str, request_id: str, duration: float, **kwargs):
        """Log para procesamiento de agentes"""
        self.logger.info("Agent Processing", extra={
            'agent_id': agent_id,
            'request_id': request_id,
            'duration': duration,
            **kwargs
        })

    def log_error(self, error_type: str, error_message: str, stack_trace: str = None, **kwargs):
        """Log para errores"""
        self.logger.error("Error", extra={
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            **kwargs
        })

    def log_performance(self, metric_name: str, value: float, unit: str, **kwargs):
        """Log para métricas de performance"""
        self.logger.info("Performance Metric", extra={
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            **kwargs
        })

# Logger global
app_logger = StructuredLogger("educational_system")

class LoggingMiddleware:
    """Middleware para logging de requests en FastAPI"""
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request_id = str(uuid.uuid4())
            start_time = datetime.now()
            
            async def receive_wrapper():
                message = await receive()
                return message
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = (datetime.now() - start_time).total_seconds()
                    status = message["status"]
                    
                    app_logger.log_request(
                        request_id=request_id,
                        method=scope["method"],
                        path=scope["path"],
                        status=status,
                        duration=duration,
                        headers=dict(scope.get("headers", {}))
                    )
                
                await send(message)
            
            await self.app(scope, receive_wrapper, send_wrapper)
        else:
            await self.app(scope, receive, send)

class MetricsCollector:
    """Colección de métricas personalizadas"""
    
    def __init__(self):
        self.metrics = {}

    def increment(self, metric_name: str, value: float = 1, tags: Dict[str, str] = None):
        """Incrementar un contador"""
        app_logger.log_performance(
            metric_name=metric_name,
            value=value,
            unit="count",
            tags=tags or {}
        )

    def gauge(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Establecer un valor de gauge"""
        app_logger.log_performance(
            metric_name=metric_name,
            value=value,
            unit="gauge",
            tags=tags or {}
        )

    def histogram(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Registrar un histograma"""
        app_logger.log_performance(
            metric_name=metric_name,
            value=value,
            unit="histogram",
            tags=tags or {}
        )

# Instancia global
collector = MetricsCollector()

# Configuración de loggers específicos
agent_logger = StructuredLogger("agent_processing")
database_logger = StructuredLogger("database_operations")
cache_logger = StructuredLogger("cache_operations")
queue_logger = StructuredLogger("queue_processing")