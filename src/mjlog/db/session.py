"""Database session and connection management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mjlog.config import get_database_url, get_hrd_url

_engine = None
_Session = None


def get_engine(db: str = "main"):
    """Get or create SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_url = get_database_url() if db == "main" else get_hrd_url()
        _engine = create_engine(db_url, echo=False)
    return _engine


def get_session_factory(db: str = "main"):
    """Get or create session factory."""
    global _Session
    if _Session is None:
        engine = get_engine(db)
        _Session = sessionmaker(bind=engine)
    return _Session


def get_session(db: str = "main"):
    """Get a new database session."""
    factory = get_session_factory(db)
    return factory()
