-- Configuración de replicación para el esclavo
-- Este script debe ejecutarse en el contenedor postgres-replica

-- Detener la replicación si existe
SELECT pg_stop_backup();

-- Configurar la réplica para que sea solo lectura
ALTER SYSTEM SET hot_standby = on;
ALTER SYSTEM SET hot_standby_feedback = on;

-- Configurar la aplicación de WAL
ALTER SYSTEM SET max_standby_streaming_delay = '30s';
ALTER SYSTEM SET wal_receiver_status_interval = '10s';
ALTER SYSTEM SET hot_standby_feedback = on;

-- Configuración de seguridad
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key';

-- Optimización para réplica de solo lectura
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.max = 10000;
ALTER SYSTEM SET pg_stat_statements.track = all;

-- Configuración de conexiones para réplica
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Configurar el archivo recovery para la réplica
-- Este comando se ejecutará automáticamente al iniciar el contenedor
-- pg_basebackup manejará la configuración de recovery.conf

-- Verificar estado de replicación
CREATE OR REPLACE VIEW replication_status AS
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
FROM pg_stat_replication;