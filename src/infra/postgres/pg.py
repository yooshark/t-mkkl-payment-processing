from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main.app_config import AppSettings, get_settings

engine: AsyncEngine = create_async_engine(
    get_settings(AppSettings).db.dsn,
    echo=get_settings(AppSettings).db.ECHO,
    connect_args={"timeout": get_settings(AppSettings).db.TIMEOUT},
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(engine, autoflush=False, expire_on_commit=False, class_=AsyncSession)
