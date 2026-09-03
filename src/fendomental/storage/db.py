from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings
from fendomental.storage.orm_models import Base

engine = create_engine(settings.db_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    return SessionLocal()


def create_all() -> None:
    """Create all tables directly from the ORM metadata.

    Used by scripts/init_db.py for a from-scratch local SQLite DB. Schema
    changes in a deployed environment should go through Alembic migrations
    instead (alembic/versions/), not this function.
    """
    Base.metadata.create_all(bind=engine)
