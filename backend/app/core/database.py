"""
Database wiring.

- `engine`     : the connection pool to Postgres.
- `SessionLocal`: a factory that hands out short-lived DB sessions.
- `Base`       : the declarative base every model inherits from.
- `get_db`     : a FastAPI dependency that yields one session per request
                 and guarantees it is closed afterwards (even on error).
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # drop dead connections instead of erroring mid-request
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """All ORM models inherit from this."""


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
