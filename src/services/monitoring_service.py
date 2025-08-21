import logging
import json
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import aiohttp
import asyncio
from datetime import datetime
import os

# Configuración de logging estructurado
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
        )
        self.logger.addHandler(console_handler)

    def log(self, level: str, message: str, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'service': 'educational_system',
            **kwargs
        }
        
        if level.upper() == 'INFO':
            self.logger.info(json.dumps(log_entry))
        elif level.upper() == 'ERROR':
            self.logger.error(json.dumps(log_entry))
        elif level.upper() == 'WARNING':
            self.logger.warning(json.dumps(log_entry))
        elif level.upper() == 'DEBUG':
            self.logger.debug(json.dumps(log_entry))

# Métricas de Prometheus
class MetricsCollector:
    def __init__(self):
        # Contadores
        self.requests_total = Counter(
            'educational_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.agent_requests_total = Counter(
            'educational_agent_requests_total',
            'Total agent requests',
            ['agent_type', 'status']
        )
        
        self.errors_total = Counter(
            'educational_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint', 'agent_type']
        )
        
        # Histogramas
        self.request_duration = Histogram(
            'educational_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.agent_response_duration = Histogram(
            'educational_agent_response_duration_seconds',
            'Agent response duration',
            ['agent_type']
        )
        
        self.database_query_duration = Histogram(
            'educational_database_query_duration_seconds',
            'Database query duration',
            ['operation', 'table']
        )
        
        # Gauges
        self.active_connections = Gauge(
            'educational_active_connections',
            'Number of active connections'
        )
        
        self.cache_hits = Gauge(
            'educational_cache_hits',
            'Cache hit rate'
        )
        
        self.queue_size = Gauge(
            'educational_queue_size',
            'Queue size',
            ['queue_name']
        )
        
        self.system_memory_usage = Gauge(
            'educational_system_memory_usage_bytes',
            'System memory usage in bytes'
        )
        
        self.system_cpu_usage = Gauge(
            'educational_system_cpu_usage_percent',
            'System CPU usage percentage'
        )

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Registrar métrica de request"""
        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_agent_request(self, agent_type: str, status: str, duration: float):
        """Registrar métrica de agente"""
        self.agent_requests_total.labels(
            agent_type=agent_type,
            status=status
        ).inc()
        
        self.agent_response_duration.labels(
            agent_type=agent_type
        ).observe(duration)

    def record_error(self, error_type: str, endpoint: str = None, agent_type: str = None):
        """Registrar métrica de error"""
        self.errors_total.labels(
            error_type=error_type,
            endpoint=endpoint or 'unknown',
            agent_type=agent_type or 'unknown'
        ).inc()

    def update_system_metrics(self):
        """Actualizar métricas del sistema"""
        try:
            import psutil
            
            # Métricas de memoria
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            
            # Métricas de CPU
            cpu_percent = psutil.cpu_percent()
            self.system_cpu_usage.set(cpu_percent)
            
            # Métricas de conexiones activas
            connections = len(psutil.net_connections())
            self.active_connections.set(connections)
            
        except ImportError:
            # Si psutil no está disponible, usar valores simulados
            self.system_memory_usage.set(1024 * 1024 * 1024)  # 1GB
            self.system_cpu_usage.set(50.0)
            self.active_connections.set(100)

# Gestor de monitoreo
class MonitoringManager:
    def __init__(self):
        self.logger = StructuredLogger('educational_monitoring')
        self.metrics = MetricsCollector()
        self.health_checks = {}

    def register_health_check(self, name: str, check_func):
        """Registrar una comprobación de salud"""
        self.health_checks[name] = check_func

    async def perform_health_checks(self) -> Dict[str, Any]:
        """Realizar todas las comprobaciones de salud"""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = time.time() - start_time
                
                health_status['checks'][name] = {
                    'status': 'ok' if result else 'failed',
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if not result:
                    health_status['status'] = 'unhealthy'
                    
            except Exception as e:
                health_status['checks'][name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                health_status['status'] = 'unhealthy'
        
        return health_status

    def log_request(self, request_data: Dict[str, Any]):
        """Registrar información de una petición"""
        self.logger.log(
            'INFO',
            'Request processed',
            method=request_data.get('method'),
            endpoint=request_data.get('endpoint'),
            user_agent=request_data.get('user_agent'),
            response_time=request_data.get('response_time'),
            status_code=request_data.get('status_code')
        )

    def log_error(self, error_data: Dict[str, Any]):
        """Registrar información de un error"""
        self.logger.log(
            'ERROR',
            error_data.get('message', 'Unknown error'),
            error_type=error_data.get('error_type'),
            endpoint=error_data.get('endpoint'),
            stack_trace=error_data.get('stack_trace'),
            user_id=error_data.get('user_id')
        )

    def log_agent_activity(self, agent_data: Dict[str, Any]):
        """Registrar actividad de agente"""
        self.logger.log(
            'INFO',
            'Agent activity',
            agent_type=agent_data.get('agent_type'),
            action=agent_data.get('action'),
            duration=agent_data.get('duration'),
            success=agent_data.get('success')
        )

    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Registrar métricas de rendimiento"""
        self.logger.log(
            'INFO',
            'Performance metrics',
            **metrics
        )

# Cliente para enviar métricas a servicios externos
class MetricsExporter:
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.getenv('METRICS_ENDPOINT')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Enviar métricas a un servicio externo"""
        if not self.endpoint:
            return False
        
        try:
            async with self.session.post(
                self.endpoint,
                json=metrics,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error enviando métricas: {e}")
            return False

# Sistema de alertas
class AlertingSystem:
    def __init__(self):
        self.thresholds = {
            'error_rate': 0.05,  # 5%
            'response_time': 2.0,  # 2 segundos
            'memory_usage': 0.85,  # 85%
            'cpu_usage': 0.9  # 90%
        }

    async def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verificar si se deben generar alertas"""
        alerts = []
        
        # Verificar tasa de errores
        if 'error_rate' in metrics and metrics['error_rate'] > self.thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate',
                'severity': 'high',
                'message': f"High error rate: {metrics['error_rate']:.2%}",
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Verificar tiempo de respuesta
        if 'avg_response_time' in metrics and metrics['avg_response_time'] > self.thresholds['response_time']:
            alerts.append({
                'type': 'response_time',
                'severity': 'medium',
                'message': f"High response time: {metrics['avg_response_time']:.2f}s",
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts

# Singleton global
monitoring_manager = MonitoringManager()

# Funciones auxiliares
async def get_prometheus_metrics() -> str:
    """Obtener métricas en formato Prometheus"""
    return generate_latest()

async def perform_system_health_check() -> Dict[str, Any]:
    """Realizar comprobación de salud del sistema"""
    return await monitoring_manager.perform_health_checks()

def setup_monitoring(app):
    """Configurar monitoreo para la aplicación FastAPI"""
    
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Registrar métricas
        monitoring_manager.metrics.record_request(
            request.method,
            request.url.path,
            response.status_code,
            process_time
        )
        
        monitoring_manager.log_request({
            'method': request.method,
            'endpoint': request.url.path,
            'user_agent': request.headers.get('user-agent'),
            'response_time': process_time,
            'status_code': response.status_code
        })
        
        return response
    
    return app

# Configuración de logging para desarrollo y producción
def configure_logging(environment: str = 'development'):
    """Configurar logging según el entorno"""
    
    if environment == 'production':
        # Logging JSON para producción
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    else:
        # Logging más detallado para desarrollo
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )