"""
Woocommerce Bot

db_manager.py
Async database manager using SQLAlchemy 2.0 async with aiosqlite.

@package    Woocommerce Bot
@subpackage Database
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    2.0.0
@link       [KiyaHolding.com]
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Base
from src.logger.log_handler import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# ─── Async Engine ────────────────────────────────────────────────────────────
# استفاده از aiosqlite برای توسعه MVP
DATABASE_URL = f"sqlite+aiosqlite:///{settings.DB_PATH}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# ─── Async Session Factory ───────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ─── Init ────────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """ساخت تمام جداول در صورت نبود (اجرای async)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized successfully (async).")
    except SQLAlchemyError as e:
        logger.error(f"❌ Database init failed: {e}")
        raise


async def get_db() -> AsyncSession:
    """
    Dependency-style async session getter.
    Usage:
        async with get_db() as db:
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
