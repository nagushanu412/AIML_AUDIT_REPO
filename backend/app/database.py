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
    return {
        "connected": True,
        "database": settings.postgres_db,
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "postgres_version": version,
    }
