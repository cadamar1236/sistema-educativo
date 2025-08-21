import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchanges = {}
        self.queues = {}

    async def connect(self):
        """Establecer conexión con RabbitMQ"""
        try:
            self.connection = await connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            logger.info("Conectado a RabbitMQ exitosamente")
        except Exception as e:
            logger.error(f"Error al conectar a RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Cerrar conexión con RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Conexión con RabbitMQ cerrada")

    async def declare_exchange(self, name: str, exchange_type: ExchangeType = ExchangeType.TOPIC):
        """Declarar un exchange"""
        if not self.channel:
            raise Exception("No hay conexión activa")
        
        exchange = await self.channel.declare_exchange(
            name, 
            type=exchange_type, 
            durable=True
        )
        self.exchanges[name] = exchange
        return exchange

    async def declare_queue(self, name: str, durable: bool = True) -> Any:
        """Declarar una cola"""
        if not self.channel:
            raise Exception("No hay conexión activa")
        
        queue = await self.channel.declare_queue(name, durable=durable)
        self.queues[name] = queue
        return queue

    async def publish_message(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """Publicar un mensaje en el exchange"""
        if exchange_name not in self.exchanges:
            await self.declare_exchange(exchange_name)
        
        exchange = self.exchanges[exchange_name]
        message_body = json.dumps(message)
        
        message_obj = Message(
            message_body.encode(),
            content_type="application/json",
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now()
        )
        
        await exchange.publish(message_obj, routing_key=routing_key)
        logger.info(f"Mensaje publicado en {exchange_name}: {message.get('type', 'unknown')}")

    async def consume_messages(self, queue_name: str, callback, auto_ack: bool = False):
        """Consumir mensajes de una cola"""
        if queue_name not in self.queues:
            await self.declare_queue(queue_name)
        
        queue = self.queues[queue_name]
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    body = json.loads(message.body.decode())
                    await callback(body)
                    if not auto_ack:
                        await message.ack()
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {e}")
                    if not auto_ack:
                        await message.reject(requeue=True)

# Gestor de colas específicas para la aplicación educativa
class EducationalQueueSystem:
    def __init__(self, queue_manager: QueueManager):
        self.queue_manager = queue_manager
        self.exchanges = {
            'student_activities': 'student.activities',
            'agent_processing': 'agent.processing',
            'notifications': 'notifications',
            'background_tasks': 'background.tasks'
        }

    async def setup_exchanges(self):
        """Configurar todos los exchanges necesarios"""
        for name in self.exchanges.values():
            await self.queue_manager.declare_exchange(name)

    async def publish_student_activity(self, student_id: str, activity: Dict[str, Any]):
        """Publicar actividad de estudiante"""
        message = {
            'type': 'student_activity',
            'student_id': student_id,
            'activity': activity,
            'timestamp': datetime.now().isoformat(),
            'priority': 'normal'
        }
        
        await self.queue_manager.publish_message(
            self.exchanges['student_activities'],
            f"student.{student_id}.activity",
            message
        )

    async def publish_agent_request(self, agent_id: str, request: Dict[str, Any]):
        """Publicar solicitud de agente"""
        message = {
            'type': 'agent_request',
            'agent_id': agent_id,
            'request': request,
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat()
        }
        
        await self.queue_manager.publish_message(
            self.exchanges['agent_processing'],
            f"agent.{agent_id}.request",
            message
        )

    async def publish_notification(self, user_id: str, notification: Dict[str, Any]):
        """Publicar notificación"""
        message = {
            'type': 'notification',
            'user_id': user_id,
            'title': notification.get('title', ''), 
            'body': notification.get('body', ''),
            'data': notification.get('data', {}),
            'priority': notification.get('priority', 'medium'),
            'timestamp': datetime.now().isoformat()
        }
        
        await self.queue_manager.publish_message(
            self.exchanges['notifications'],
            f"user.{user_id}.notification",
            message
        )

    async def schedule_background_task(self, task_type: str, data: Dict[str, Any], delay: int = 0):
        """Programar tarea en segundo plano"""
        message = {
            'type': 'background_task',
            'task_type': task_type,
            'data': data,
            'scheduled_at': datetime.now().isoformat(),
            'delay': delay,
            'task_id': str(uuid.uuid4())
        }
        
        routing_key = f"task.{task_type}"
        if delay > 0:
            routing_key += f".delayed.{delay}"
        
        await self.queue_manager.publish_message(
            self.exchanges['background_tasks'],
            routing_key,
            message
        )

# Worker para procesamiento asíncrono
class WorkerService:
    def __init__(self, queue_system: EducationalQueueSystem):
        self.queue_system = queue_system
        self.running = False

    async def start(self):
        """Iniciar el worker"""
        self.running = True
        await self.queue_system.setup_exchanges()
        
        # Configurar colas de consumo
        await self.queue_system.queue_manager.declare_queue('student_activities')
        await self.queue_system.queue_manager.declare_queue('agent_responses')
        await self.queue_system.queue_manager.declare_queue('notifications')
        await self.queue_system.queue_manager.declare_queue('background_tasks')
        
        # Iniciar consumidores
        await asyncio.gather(
            self.consume_student_activities(),
            self.consume_agent_responses(),
            self.consume_notifications(),
            self.consume_background_tasks()
        )

    async def stop(self):
        """Detener el worker"""
        self.running = False

    async def consume_student_activities(self):
        """Procesar actividades de estudiantes"""
        async def process_activity(message: Dict[str, Any]):
            from src.services.student_stats_service import student_stats_service
            
            student_id = message.get('student_id')
            activity = message.get('activity')
            
            if student_id and activity:
                await student_stats_service.update_student_activity_async(student_id, activity)
                logger.info(f"Actividad procesada para estudiante {student_id}")

        await self.queue_system.queue_manager.consume_messages(
            'student_activities',
            process_activity
        )

    async def consume_agent_responses(self):
        """Procesar respuestas de agentes"""
        async def process_agent_response(message: Dict[str, Any]):
            # Procesar respuesta del agente
            agent_id = message.get('agent_id')
            request = message.get('request')
            
            logger.info(f"Procesando respuesta de agente {agent_id}")
            # Aquí se puede agregar lógica adicional de procesamiento

        await self.queue_system.queue_manager.consume_messages(
            'agent_responses',
            process_agent_response
        )

    async def consume_notifications(self):
        """Procesar notificaciones"""
        async def process_notification(message: Dict[str, Any]):
            user_id = message.get('user_id')
            notification = {
                'title': message.get('title'),
                'body': message.get('body'),
                'data': message.get('data')
            }
            
            # Aquí se puede integrar con servicios de notificación (email, push, etc.)
            logger.info(f"Notificación enviada a usuario {user_id}")

        await self.queue_system.queue_manager.consume_messages(
            'notifications',
            process_notification
        )

    async def consume_background_tasks(self):
        """Procesar tareas en segundo plano"""
        async def process_background_task(message: Dict[str, Any]):
            task_type = message.get('task_type')
            data = message.get('data')
            
            logger.info(f"Procesando tarea en segundo plano: {task_type}")
            
            if task_type == 'cleanup_cache':
                await self.cleanup_cache(data)
            elif task_type == 'generate_report':
                await self.generate_report(data)
            elif task_type == 'update_statistics':
                await self.update_statistics(data)

        await self.queue_system.queue_manager.consume_messages(
            'background_tasks',
            process_background_task
        )

    async def cleanup_cache(self, data: Dict[str, Any]):
        """Limpiar caché antiguo"""
        # Implementar lógica de limpieza de caché
        logger.info("Limpiando caché antiguo")

    async def generate_report(self, data: Dict[str, Any]):
        """Generar reportes"""
        # Implementar lógica de generación de reportes
        logger.info("Generando reporte")

    async def update_statistics(self, data: Dict[str, Any]):
        """Actualizar estadísticas"""
        # Implementar lógica de actualización de estadísticas
        logger.info("Actualizando estadísticas")

# Gestor de colas global
queue_manager = QueueManager()
educational_queue_system = EducationalQueueSystem(queue_manager)

async def initialize_queue_system():
    """Inicializar el sistema de colas"""
    await queue_manager.connect()
    await educational_queue_system.setup_exchanges()

async def close_queue_system():
    """Cerrar el sistema de colas"""
    await queue_manager.disconnect()

# Decorador para publicar eventos
async def publish_event(event_type: str, data: Dict[str, Any]):
    """Publicar un evento en el sistema de colas"""
    await educational_queue_system.queue_manager.publish_message(
        'events',
        f"event.{event_type}",
        data
    )