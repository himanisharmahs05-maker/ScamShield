from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


import socket

def _is_service_listening(host="localhost", port=5432) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False

_raw_db_url = os.environ.get("DATABASE_URL")
if not _raw_db_url:
    if _is_service_listening("127.0.0.1", 5432) or _is_service_listening("localhost", 5432):
        _DATABASE_URL = "postgresql+asyncpg://safenav_user:safenav_password@localhost:5432/safenav_db"
    else:
        _DATABASE_URL = "sqlite+aiosqlite:///./scamshield.db"
else:
    _DATABASE_URL = _raw_db_url

_use_null_pool = os.environ.get("DB_NULL_POOL", "false").lower() == "true"

_engine_kwargs: dict = {
    "echo": os.environ.get("DB_ECHO", "false").lower() == "true",
    "future": True,
}

if "sqlite" not in _DATABASE_URL:
    _POOL_SIZE: int = int(os.environ.get("DB_POOL_SIZE", "10"))
    _MAX_OVERFLOW: int = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
    _POOL_TIMEOUT: int = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
    _POOL_RECYCLE: int = int(os.environ.get("DB_POOL_RECYCLE", "1800"))
    _engine_kwargs["pool_pre_ping"] = True
    if _use_null_pool:
        _engine_kwargs["poolclass"] = NullPool
    else:
        _engine_kwargs.update({
            "pool_size": _POOL_SIZE,
            "max_overflow": _MAX_OVERFLOW,
            "pool_timeout": _POOL_TIMEOUT,
            "pool_recycle": _POOL_RECYCLE,
        })

engine: AsyncEngine = create_async_engine(_DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    await engine.dispose()