from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_database_connection() -> dict:
    """Verify PostgreSQL connectivity at startup."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar_one()
        conn.execute(text("SELECT 1"))
    db_label = (
        "DATABASE_URL"
        if settings.database_url
        else settings.postgres_db
    )
    host_label = (
        "DATABASE_URL"
        if settings.database_url
        else settings.postgres_host
    )
    return {
        "connected": True,
        "database": db_label,
        "host": host_label,
        "port": settings.postgres_port if not settings.database_url else None,
        "postgres_version": version,
    }
