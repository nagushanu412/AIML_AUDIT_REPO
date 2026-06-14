import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, validate_database_connection
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.clients import router as clients_router
from app.routers.dashboard import router as dashboard_router
from app.routers.engagements import router as engagements_router
from app.routers.health import router as health_router
from app.routers.projects import router as projects_router
from app.routers.rules import router as rules_router
from app.routers.rules_master import router as rules_master_router
from app.routers.upload import router as upload_router
from app.services.seed_service import seed_demo_hierarchy

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        info = validate_database_connection()
        logger.info(
            "Database connected: %s@%s:%s/%s",
            settings.postgres_user,
            info["host"],
            info["port"],
            info["database"],
        )
        db = SessionLocal()
        try:
            seed_demo_hierarchy(db)
            logger.info("Demo hierarchy seed completed")
        finally:
            db.close()
    except Exception:
        logger.exception("Startup database connection validation failed")
        raise
    yield


app = FastAPI(
    title="AIML Audit Analytics Platform API",
    description=(
        "Backend API for AIML Audit Analytics.\n\n"
        "## Hierarchy\n"
        "Auditor → Clients → Engagements → Projects → Upload → Rules → Risk → Findings → Reports\n\n"
        "Interactive docs: `/docs` (Swagger) · `/redoc`"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(engagements_router)
app.include_router(projects_router)
app.include_router(upload_router)
app.include_router(rules_router)
app.include_router(rules_master_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)
