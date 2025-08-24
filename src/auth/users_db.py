"""Persistencia de usuarios y roles.

Actualmente soporta SQLite y Postgres (solo cambiar DATABASE_URL).

Para escalar a miles de usuarios:
 - Usa Postgres: export DATABASE_URL=postgresql+psycopg://user:pass@host/db
 - Añade Alembic para migraciones.
 - Considera conexión pool size e.g. create_engine(..., pool_size=10, max_overflow=20)
 - Índices ya definidos en columnas críticas (id, email, role).
"""
from __future__ import annotations
import os
from datetime import datetime
from typing import Iterable
from sqlalchemy import create_engine, Column, String, DateTime, select
from sqlalchemy.orm import declarative_base, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/users.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
    pool_pre_ping=True,
)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    role = Column(String, default="student", index=True)
    subscription_tier = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

_initialized = False
def init_db():
    global _initialized
    if _initialized:
        return
    # Nota: Con Alembic en producción, preferir ejecutar migraciones en lugar de create_all.
    Base.metadata.create_all(engine)
    _initialized = True

def get_session() -> Session:
    return Session(engine, future=True)

def get_or_create_from_google(google_user: dict, role: str, subscription_tier: str) -> User:
    try:
        init_db()
        with get_session() as session:
            stmt = select(User).where(User.id == google_user["id"])
            existing = session.execute(stmt).scalar_one_or_none()
            if existing:
                changed = False
                for field in ["email", "name", "picture"]:
                    val = google_user.get(field)
                    if val and getattr(existing, field) != val:
                        setattr(existing, field, val); changed = True
                if existing.role != role:
                    existing.role = role; changed = True
                if existing.subscription_tier != subscription_tier:
                    existing.subscription_tier = subscription_tier; changed = True
                if changed:
                    session.add(existing)
                    session.commit()
                    session.refresh(existing)
                return existing
            u = User(
                id=google_user["id"],
                email=google_user["email"],
                name=google_user.get("name", ""),
                picture=google_user.get("picture"),
                role=role,
                subscription_tier=subscription_tier,
            )
            session.add(u)
            session.commit()
            session.refresh(u)
            return u
    except Exception as e:
        # Si la base de datos falla, crear un objeto User temporal sin persistir
        import logging
        logging.getLogger(__name__).warning(f"Database connection failed, creating temporary user: {e}")
        
        # Crear un User object que no depende de la DB
        class TempUser:
            def __init__(self, id, email, name, picture, role, subscription_tier):
                self.id = id
                self.email = email  
                self.name = name
                self.picture = picture
                self.role = role
                self.subscription_tier = subscription_tier
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
        
        return TempUser(
            id=google_user["id"],
            email=google_user["email"],
            name=google_user.get("name", ""),
            picture=google_user.get("picture"),
            role=role,
            subscription_tier=subscription_tier,
        )

def update_role(email: str, role: str) -> bool:
    init_db()
    with get_session() as session:
        stmt = select(User).where(User.email == email)
        u = session.execute(stmt).scalar_one_or_none()
        if not u:
            return False
        u.role = role
        session.add(u)
        session.commit()
        return True

def list_teachers() -> Iterable[User]:
    init_db()
    with get_session() as session:
        stmt = select(User).where(User.role == "teacher")
        return [row for row in session.execute(stmt).scalars().all()]
