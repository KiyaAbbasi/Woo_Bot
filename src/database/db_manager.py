"""
Woocommerce Bot

db_manager.py
Database connection manager using SQLAlchemy

@package    Woocommerce Bot
@subpackage Database
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Base
from src.logger.log_handler import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# ─── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    f"sqlite:///{settings.DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

# ─── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ─── Init ──────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """ساخت تمام جداول در صورت نبود"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully.")
    except SQLAlchemyError as e:
        logger.error(f"❌ Database init failed: {e}")
        raise


def get_db() -> Session:
    """
    Dependency-style session getter.
    Usage:
        db = get_db()
        try:
            ...
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        return db
    except SQLAlchemyError as e:
        db.close()
        logger.error(f"❌ DB session error: {e}")
        raise