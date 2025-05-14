"""
Inicializa o engine assíncrono e o sessionmaker padrão do projeto.
Utiliza settings (Dynaconf) + variáveis de ambiente como fallback.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from app.config import env

# ---------------------------------------
# 🔧 Montagem da URL de conexão
# ---------------------------------------
def _get_database_url() -> str:
    """
    Prioridade:
    1. Variável de ambiente POSTGRES_URL
    2. Dynaconf settings.POSTGRES_URL
       (aceita 'postgresql+asyncpg://' ou 'postgres://' e converte)
    """
    url = os.getenv("POSTGRES_URL") or env.get("POSTGRES_URL")
    if not url:
        raise RuntimeError(
            "POSTGRES_URL não definido em variáveis de ambiente nem em settings"
        )

    # garante driver asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


DATABASE_URL: str = _get_database_url()

# ---------------------------------------
# 🔌 Engine e sessionmaker assíncronos
# ---------------------------------------
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,           # → True para debug SQL
    pool_pre_ping=True,   # evita erros de conexões ociosas
    future=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


# ---------------------------------------
# 📦 Dependency de sessão para FastAPI
# ---------------------------------------
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# ---------------------------------------
# 🗺️ Declarative base
# ---------------------------------------
Base = declarative_base()

