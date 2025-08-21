-- Configuración de replicación maestro-esclavo
-- Este script debe ejecutarse en el contenedor postgres-primary

-- Crear usuario para replicación
CREATE USER replica WITH REPLICATION PASSWORD 'replica_password_2024';

-- Crear base de datos principal
CREATE DATABASE educational_system OWNER admin;

-- Configurar permisos
GRANT ALL PRIVILEGES ON DATABASE educational_system TO admin;

-- Configurar esquema de auditoría para monitoreo
CREATE SCHEMA IF NOT EXISTS audit;

-- Tabla de auditoría
CREATE TABLE IF NOT EXISTS audit.logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(20),
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_audit_table_name ON audit.logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON audit.logs(changed_at);

-- Configurar particionado para tablas grandes
CREATE TABLE IF NOT EXISTS student_activities (
    id UUID PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    activity_type VARCHAR(50),
    activity_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Crear particiones mensuales
CREATE TABLE IF NOT EXISTS student_activities_2024_01 PARTITION OF student_activities
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS student_activities_2024_02 PARTITION OF student_activities
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Índices optimizados
CREATE INDEX IF NOT EXISTS idx_student_activities_student_id ON student_activities(student_id);
CREATE INDEX IF NOT EXISTS idx_student_activities_created_at ON student_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_student_activities_type ON student_activities(activity_type);

-- Índices GIN para JSONB
CREATE INDEX IF NOT EXISTS idx_student_activities_data ON student_activities USING GIN (activity_data);

-- Configuración de conexiones
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Configuración para replicación
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET max_replication_slots = 3;
ALTER SYSTEM SET hot_standby = on;