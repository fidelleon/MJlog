"""Configuration: Load and validate environment settings."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_config():
    """Load environment variables from mjlog.env."""
    # Find mjlog.env in the project root (parent of src/)
    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / "mjlog.env"
    if not env_file.exists():
        raise FileNotFoundError(f"mjlog.env not found at {env_file}")
    load_dotenv(env_file)


def get_database_url() -> str:
    """Get PostgreSQL connection URL from environment."""
    load_config()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set in mjlog.env")
    return db_url


def get_hrd_url() -> str:
    """Get MySQL connection URL from environment."""
    load_config()
    db_url = os.getenv("HRD_DATABASE_URL")
    if not db_url:
        raise ValueError("HRD_DATABASE_URL not set in mjlog.env")
    return db_url
