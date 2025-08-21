# Configuración de producción

from pydantic import BaseSettings
from typing import Optional
import os

class ProductionSettings(BaseSettings):
    # Configuración de base de datos
    database_url: str = os.getenv("DATABASE_URL", "postgresql://admin:password@postgres-primary:5432/educational_system")
    replica_database_url: str = os.getenv("REPLICA_DATABASE_URL", "postgresql://admin:password@postgres-replica:5432/educational_system")
    
    # Configuración de Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://default:password@redis-master:6379/0")
    redis_slave_url: str = os.getenv("REDIS_SLAVE_URL", "redis://default:password@redis-slave:6379/0")
    
    # Configuración de RabbitMQ
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://admin:password@rabbitmq:5672/")
    
    # Configuración de API
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))
    api_workers: int = int(os.getenv("WORKERS", "4"))
    
    # Configuración de seguridad
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # Configuración de Groq
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    groq_temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    groq_max_tokens: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))
    
    # Configuración de monitoreo
    prometheus_port: int = 9090
    grafana_port: int = 3000
    kibana_port: int = 5601
    
    # Configuración de entorno
    environment: str = "production"
    debug: bool = False
    testing: bool = False
    
    # Configuración de archivos
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: list = ["pdf", "docx", "txt", "jpg", "png", "mp4"]
    
    # Configuración de rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Configuración de caché
    cache_ttl: int = 3600  # 1 hora
    cache_max_size: int = 1000  # 1000 items
    
    # Configuración de backup
    backup_enabled: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    backup_schedule: str = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # Daily at 2 AM
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    
    # Configuración de logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "json"
    log_file: str = "/app/logs/educational_system.log"
    
    # Configuración de CORS
    cors_origins: list = [
        "https://localhost:3000",
        "https://educational-system.com",
        "https://*.educational-system.com"
    ]
    
    # Configuración de seguridad
    ssl_enabled: bool = True
    ssl_cert_path: str = "/etc/ssl/certs/cert.pem"
    ssl_key_path: str = "/etc/ssl/private/key.pem"
    
    # Configuración de email (para notificaciones)
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = True
    
    # Configuración de AWS (si se usa)
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    
    # Configuración de Azure (si se usa)
    azure_storage_account: str = os.getenv("AZURE_STORAGE_ACCOUNT", "")
    azure_storage_key: str = os.getenv("AZURE_STORAGE_KEY", "")
    azure_container: str = os.getenv("AZURE_CONTAINER", "")
    
    # Configuración de Google Cloud (si se usa)
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    gcp_storage_bucket: str = os.getenv("GCP_STORAGE_BUCKET", "")
    gcp_service_account_key: str = os.getenv("GCP_SERVICE_ACCOUNT_KEY", "")
    
    # Configuración de CDN
    cdn_enabled: bool = os.getenv("CDN_ENABLED", "false").lower() == "true"
    cdn_url: str = os.getenv("CDN_URL", "")
    
    # Configuración de Webhooks
    webhook_url: str = os.getenv("WEBHOOK_URL", "")
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instancia global de configuración
settings = ProductionSettings()

# Validación de configuración
def validate_configuration():
    """Validar que la configuración es válida"""
    errors = []
    
    if not settings.groq_api_key:
        errors.append("GROQ_API_KEY es requerido")
    
    if settings.environment == "production" and settings.debug:
        errors.append("DEBUG debe ser False en producción")
    
    if settings.ssl_enabled and (not settings.ssl_cert_path or not settings.ssl_key_path):
        errors.append("SSL_CERT_PATH y SSL_KEY_PATH son requeridos cuando SSL_ENABLED es True")
    
    if errors:
        raise ValueError(f"Configuración inválida: {', '.join(errors)}")
    
    return True

# Funciones de utilidad
def get_database_config():
    """Obtener configuración de base de datos"""
    return {
        "url": settings.database_url,
        "replica_url": settings.replica_database_url,
        "pool_size": 20,
        "max_overflow": 30,
        "pool_pre_ping": True,
        "echo": settings.debug
    }

def get_redis_config():
    """Obtener configuración de Redis"""
    return {
        "url": settings.redis_url,
        "slave_url": settings.redis_slave_url,
        "decode_responses": True,
        "socket_keepalive": True,
        "socket_keepalive_options": {}
    }

def get_security_config():
    """Obtener configuración de seguridad"""
    return {
        "secret_key": settings.secret_key,
        "algorithm": settings.algorithm,
        "access_token_expire_minutes": settings.access_token_expire_minutes,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "rate_limit_per_hour": settings.rate_limit_per_hour
    }

if __name__ == "__main__":
    validate_configuration()
    print("Configuración válida")