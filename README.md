## Sistema Educativo Multiagente

### Arranque rápido

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg://user:pass@localhost/db  # Opcional (si no, usa SQLite)
set REDIS_URL=redis://localhost:6379/0  # Opcional para caché
python run_server.py
```

### Migraciones Alembic automáticas
Al iniciar `run_server.py` se ejecuta (si `RUN_DB_MIGRATIONS=true`) un `alembic upgrade head`. Desactiva exportando:
```
set RUN_DB_MIGRATIONS=false
```

### Variables de entorno
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| DATABASE_URL | Cadena SQLAlchemy (Postgres recomendado) | postgresql+psycopg://user:pass@host/db |
| REDIS_URL | Conexión Redis para caché de stats | redis://localhost:6379/0 |
| RUN_DB_MIGRATIONS | Ejecutar migraciones en arranque | true |

### Caché de dashboard
Endpoint `/api/students/{student_id}/dashboard-stats` usa Redis (si disponible) con TTL aleatorio 60–120s. Respuesta incluye campo `"cache": true/false`.

Si Redis no está disponible, el endpoint responde normalmente sin caché.
