import os

from sqlmodel import SQLModel, create_engine


_engine = None


def get_engine():
    """Create the database engine lazily so tests can configure DATABASE_URL first."""
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./nomad_ai.db")
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _engine = create_engine(database_url, echo=False, connect_args=connect_args)
    return _engine


def create_db_and_tables():
    SQLModel.metadata.create_all(get_engine())
