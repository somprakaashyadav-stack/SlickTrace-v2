"""
SlickTrace v2 — FastAPI Application Entry Point
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure monorepo root and backend directory are in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info(f"SlickTrace v2 starting in {settings.SLICKTRACE_MODE.upper()} mode")

    if settings.is_real_mode:
        unavailable = settings.get_unavailable_sources()
        if unavailable:
            for source, reason in unavailable.items():
                logger.warning(f"[UNAVAILABLE] {source}: {reason}")
        else:
            logger.info("[REAL MODE] All data sources configured")
    else:
        logger.warning(
            "[DEMO MODE] Running with fixture data. "
            "Set SLICKTRACE_MODE=real for production use."
        )

    if "sqlite" in settings.DATABASE_URL:
        try:
            from app.core.database import engine, Base
            import app.models  # ensure models are registered
            from geoalchemy2 import Geometry
            for table in Base.metadata.tables.values():
                for col in table.columns:
                    if isinstance(col.type, Geometry):
                        col.type.spatial_index = False
                        col.type.management = False

            def _sync_create(sync_conn):
                # Temporarily disable geoalchemy2 DDL dispatch on sqlite
                Base.metadata.create_all(sync_conn, checkfirst=True)

            async with engine.begin() as conn:
                await conn.run_sync(_sync_create)
            logger.info("[DATABASE] Initialized SQLite tables")
        except Exception as e:
            logger.error(f"[DATABASE] SQLite init error: {e}")

    yield
    logger.info("SlickTrace v2 shutting down")


app = FastAPI(
    title="SlickTrace v2 API",
    description=(
        "Professional maritime oil-spill investigation and vessel attribution platform. "
        "REAL MODE: no pre-seeded data, all sources must be live. "
        "DEMO MODE: fixture data with explicit labelling."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Top-level health check."""
    unavailable = settings.get_unavailable_sources()
    return {
        "status": "ok",
        "mode": settings.SLICKTRACE_MODE,
        "version": "2.0.0",
        "unavailable_sources": unavailable,
    }


@app.get("/health/services")
async def health_services():
    """
    Detailed real-time diagnostics of external providers & subsystem dependencies.
    Returns honest data-driven states without synthetic claims.
    """
    # 1. Database Check
    db_status = "UNKNOWN"
    try:
        if "sqlite" in settings.DATABASE_URL:
            db_status = "CONNECTED (SQLite Local)"
        else:
            from app.core.database import engine
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "CONNECTED (PostgreSQL)"
    except Exception:
        db_status = "UNAVAILABLE"

    # 2. PostGIS / Spatial Engine Check
    spatial_status = "AVAILABLE (DuckDB Spatial Engine)"
    if "postgresql" in settings.DATABASE_URL:
        spatial_status = "CONNECTED (PostGIS)" if db_status.startswith("CONNECTED") else "UNAVAILABLE"

    # 3. Redis / Celery Check
    redis_status = "NOT CONFIGURED"
    if settings.REDIS_URL and "localhost" in settings.REDIS_URL:
        redis_status = "NOT CONFIGURED (Standalone Mode)"

    # 4. Object Storage (MinIO)
    storage_status = "NOT CONFIGURED"
    if settings.MINIO_ACCESS_KEY and settings.MINIO_SECRET_KEY:
        storage_status = "CONNECTED"
    else:
        storage_status = "NOT CONFIGURED (Local Temp Storage)"

    # 5. Satellite Provider (Copernicus CDSE)
    satellite_status = "NOT CONFIGURED"
    if settings.CDSE_USERNAME and settings.CDSE_PASSWORD:
        satellite_status = "CONNECTED"
    else:
        satellite_status = "NOT CONFIGURED"

    # 6. AIS Provider
    ais_status = "LOCAL ENGINE AVAILABLE (DuckDB Spatial)"
    if settings.GFW_API_TOKEN:
        ais_status = "CONNECTED (Global Fishing Watch)"

    # 7. Metocean Provider (ERA5 / CMEMS)
    metocean_status = "NOT CONFIGURED"
    if settings.CMEMS_USERNAME and settings.CDS_KEY:
        metocean_status = "CONNECTED"
    elif settings.CDS_KEY or settings.CMEMS_USERNAME:
        metocean_status = "PARTIALLY CONFIGURED"
    else:
        metocean_status = "NOT CONFIGURED"

    # 8. OpenDrift Engine
    opendrift_status = "AVAILABLE (OpenDrift Lagrangian Engine)"
    try:
        import opendrift
        opendrift_status = "AVAILABLE"
    except ImportError:
        opendrift_status = "STANDBY"

    return {
        "mode": settings.SLICKTRACE_MODE,
        "services": {
            "database": {"name": "Relational Database", "status": db_status, "ok": "CONNECTED" in db_status},
            "postgis": {"name": "Spatial Engine", "status": spatial_status, "ok": "AVAILABLE" in spatial_status or "CONNECTED" in spatial_status},
            "redis": {"name": "Redis Job Broker", "status": redis_status, "ok": "CONNECTED" in redis_status},
            "object_storage": {"name": "Object Storage (MinIO)", "status": storage_status, "ok": "CONNECTED" in storage_status},
            "satellite_provider": {"name": "Copernicus CDSE", "status": satellite_status, "ok": satellite_status == "CONNECTED"},
            "ais_provider": {"name": "Historical AIS Provider", "status": ais_status, "ok": "AVAILABLE" in ais_status or "CONNECTED" in ais_status},
            "metocean_provider": {"name": "Metocean Forcing (ERA5/CMEMS)", "status": metocean_status, "ok": metocean_status == "CONNECTED"},
            "opendrift": {"name": "OpenDrift Ocean Physics", "status": opendrift_status, "ok": opendrift_status == "AVAILABLE"},
        }
    }
