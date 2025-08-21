#!/usr/bin/env python3
"""
Simple server launcher for the educational library system
"""

import sys
import os
import uvicorn, os, subprocess, sys
from pathlib import Path
from pathlib import Path
try:
    from dotenv import load_dotenv  # optional
except ImportError:
    load_dotenv = None

def run_migrations_on_startup():
    if os.getenv("RUN_DB_MIGRATIONS", "true").lower() == "true":
        # Simple heuristic: if users table missing when using Postgres, run upgrade
        try:
            print("▶ Ejecutando migraciones Alembic (si es necesario)...")
            subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)
        except Exception as e:
            print(f"⚠️ No se pudieron ejecutar migraciones automáticamente: {e}")

def ensure_database_exists():
    """Crear la base de datos destino si aún no existe (PostgreSQL).

    evita fallo FATAL: database "X" does not exist al correr migraciones.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        return
    try:
        from sqlalchemy.engine.url import make_url
        from sqlalchemy import create_engine, text
        parsed = make_url(url)
        if parsed.get_backend_name() not in ("postgresql", "postgresql+psycopg"):
            return
        target_db = parsed.database
        # Conectar a postgres para verificar/crear
        admin_url = parsed.set(database="postgres")
        # AUTOCOMMIT para CREATE DATABASE
        eng = create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True, future=True)
        with eng.connect() as conn:
            exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :d"), {"d": target_db}).scalar()
            if not exists:
                print(f"🛠️ Creando base de datos '{target_db}' en el servidor...")
                conn.execute(text(f'CREATE DATABASE "{target_db}"'))
                print("✅ Base de datos creada")
    except Exception as e:
        print(f"⚠️ No se pudo verificar/crear la base de datos: {e}")

# Añadir dinámicamente el directorio del proyecto y src al PYTHONPATH (portátil)
BASE_DIR = Path(__file__).parent.resolve()
SRC_DIR = BASE_DIR / 'src'
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if __name__ == "__main__":
    # Cargar variables de entorno desde .env si existe
    if load_dotenv:
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
    # Asegurar que la BD existe antes de migrar (solo Postgres)
    ensure_database_exists()
    run_migrations_on_startup()
    # Set environment variables
    # Ajustar PYTHONPATH solo para la sesión actual
    os.environ['PYTHONPATH'] = str(BASE_DIR)
    
    print("🚀 Starting Educational Library System with Unified Wrapper")
    print("=" * 60)
    print("✅ Library service wrapper is active")
    print("✅ Automatic parameter handling enabled")
    print("✅ Support for 20+ file types")
    print("=" * 60)
    if os.getenv("DISABLE_REDIS_CACHE", "false").lower() == "true":
        print("ℹ️ Redis cache deshabilitado por DISABLE_REDIS_CACHE=true")
    else:
        try:
            import redis  # noqa: F401
            print("🧠 Redis cache activo (si servidor disponible)")
        except ImportError:
            print("⚠️ Paquete 'redis' no instalado: caching desactivado (pip install redis)")
    
    # Start the server
    uvicorn.run(
        "src.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )