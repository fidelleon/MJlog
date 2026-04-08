"""Shared pytest fixtures and configuration for MJlog tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mjlog.db.models import Base
from mjlog.db.session import get_session, get_session_factory, get_engine


@pytest.fixture(scope="session")
def test_db_engine():
    """Create an in-memory SQLite database engine for testing.
    
    Uses SQLite in-memory database to avoid needing PostgreSQL running
    during tests. All tables are created fresh for the test session.
    
    Yields:
        sqlalchemy.engine.Engine: In-memory database engine.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Create all tables based on models
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine):
    """Create a new database session for each test.
    
    Provides a fresh database session that is rolled back after each test
    to ensure test isolation.
    
    Args:
        test_db_engine: Session-scoped database engine fixture.
    
    Yields:
        sqlalchemy.orm.session.Session: Database session for testing.
    """
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    session = SessionLocal()
    
    yield session
    
    # Clean up: rollback any uncommitted changes
    session.rollback()
    
    # Remove all rows from all tables to ensure test isolation
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(text(f"DELETE FROM {table.name}"))
    
    session.commit()
    session.close()


@pytest.fixture
def app_config(monkeypatch, tmp_path):
    """Mock application configuration.
    
    Sets up environment variables and configuration paths for testing
    without affecting the actual configuration files.
    
    Args:
        monkeypatch: pytest monkeypatch fixture for env vars.
        tmp_path: pytest temporary directory fixture.
    
    Yields:
        dict: Configuration dictionary with test settings.
    """
    config = {
        "DATABASE_URL": "sqlite:///:memory:",
        "DATA_DIR": str(tmp_path),
        "LOG_LEVEL": "DEBUG",
    }
    
    # Mock environment variables
    for key, value in config.items():
        monkeypatch.setenv(key, str(value))
    
    yield config


@pytest.fixture
def mock_qapp():
    """Create a mock QApplication for testing PySide6 components.
    
    Provides a QApplication instance for GUI tests without requiring
    an actual display.
    
    Yields:
        MagicMock: Mocked QApplication instance.
    """
    mock_app = MagicMock()
    mock_app.exec = MagicMock(return_value=0)
    
    yield mock_app


@pytest.fixture
def mock_http_requests(requests_mock):
    """Fixture for mocking HTTP requests.
    
    Uses responses library to mock HTTP requests without making actual
    network calls.
    
    Args:
        requests_mock: requests-mock plugin fixture.
    
    Yields:
        requests_mock.Mocker: HTTP request mocker.
    """
    yield requests_mock
