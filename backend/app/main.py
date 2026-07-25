import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, validate_database_connection
import app.models.organization_id_events  # noqa: F401 — register org_id before_insert
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.clients import router as clients_router
from app.routers.dashboard import router as dashboard_router
from app.routers.engagement_team import router as engagement_team_router
from app.routers.analysis_runs import router as analysis_runs_router
from app.routers.engagement_hub import router as engagement_hub_router
from app.routers.evidence import router as evidence_router
from app.routers.finding_lifecycle import router as finding_lifecycle_router
from app.routers.review_workflow import router as review_workflow_router
from app.routers.workpapers import router as workpapers_router
from app.routers.engagements import router as engagements_router
from app.routers.health import router as health_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.engagement_modules import router as engagement_modules_router
from app.routers.generic_modules import router as generic_modules_router
from app.routers.module_catalog import router as module_catalog_router
from app.routers.organization_members import router as organization_members_router
from app.routers.organizations import router as organizations_router
from app.routers.projects import router as projects_router
from app.routers.procurement import router as procurement_router
from app.routers.revenue import router as revenue_router
from app.routers.rules import router as rules_router
from app.routers.rules_master import router as rules_master_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.upload import router as upload_router
from app.services.seed_service import seed_demo_hierarchy

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        info = validate_database_connection()
        logger.info(
            "Database connected: %s (env=%s)",
            info["database"],
            settings.environment,
        )
        if settings.is_production and settings.uses_default_jwt_secret:
            logger.warning(
                "JWT_SECRET_KEY is still the default — set a strong secret in production."
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
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(organization_members_router)
app.include_router(subscriptions_router)
app.include_router(module_catalog_router)
app.include_router(generic_modules_router)
app.include_router(clients_router)
app.include_router(engagements_router)
app.include_router(engagement_team_router)
app.include_router(engagement_hub_router)
app.include_router(analysis_runs_router)
app.include_router(review_workflow_router)
app.include_router(finding_lifecycle_router)
app.include_router(evidence_router)
app.include_router(workpapers_router)
app.include_router(engagement_modules_router)
app.include_router(projects_router)
app.include_router(upload_router)
app.include_router(revenue_router)
app.include_router(procurement_router)
app.include_router(rules_router)
app.include_router(rules_master_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)
app.include_router(audit_logs_router)
