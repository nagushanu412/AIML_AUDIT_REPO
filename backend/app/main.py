import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import validate_database_connection
from app.routers.health import router as health_router
from app.routers.upload import router as upload_router

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
    except Exception:
        logger.exception("Startup database connection validation failed")
        raise
    yield


app = FastAPI(
    title="AIML Audit Analytics Platform API",
    description="Backend API for audit analytics — foundation layer",
    version="1.0.0",
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
app.include_router(upload_router)
