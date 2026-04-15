from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from graph.config import get_settings
from graph.db.models import Base

logger = logging.getLogger("support_api")

_FALLBACK_URI = "sqlite:///./support_agent.db"


def _get_uri() -> str:
    uri = get_settings().postgres_uri
    if not uri:
        logger.warning("POSTGRES_URI not set — using SQLite fallback: %s", _FALLBACK_URI)
        return _FALLBACK_URI
    return uri


engine = create_engine(
    _get_uri(),
    connect_args={"check_same_thread": False} if "sqlite" in _get_uri() else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("DB tables created (if not exist)")
