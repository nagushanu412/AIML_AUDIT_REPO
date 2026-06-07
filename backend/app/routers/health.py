from fastapi import APIRouter, HTTPException
from sqlalchemy import inspect

from app.config import get_settings
from app.database import engine, validate_database_connection

router = APIRouter(tags=["Health"])

REQUIRED_TABLES = [
    "users",
    "audit_projects",
    "journal_entries",
    "rule_results",
    "risk_scores",
    "audit_findings",
]


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AIML Audit Analytics API",
    }


@router.get("/health/db")
def health_db():
    settings = get_settings()
    try:
        conn_info = validate_database_connection()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Database connection failed",
                "error": str(exc),
                "database": settings.postgres_db,
                "host": settings.postgres_host,
            },
        ) from exc

    with engine.connect() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        missing_tables = [t for t in REQUIRED_TABLES if t not in existing_tables]

    return {
        "status": "ok" if not missing_tables else "degraded",
        "database": conn_info["database"],
        "host": conn_info["host"],
        "port": conn_info["port"],
        "postgres_version": conn_info["postgres_version"],
        "tables": {
            "required": REQUIRED_TABLES,
            "existing": sorted(existing_tables.intersection(REQUIRED_TABLES)),
            "missing": missing_tables,
        },
        "migrations_applied": len(missing_tables) == 0,
    }
