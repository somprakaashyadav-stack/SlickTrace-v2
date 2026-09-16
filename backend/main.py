from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.config import settings
from backend.database import init_db
from backend.routers import (
    health, demo, spills, drift, ais, suspects, verification, reports
)
from backend.services.satellite import routes as satellite_routes
from backend.services.detection import routes as detection_routes
from backend.services.characterization import routes as characterization_routes
from backend.services.drift import routes as drift_routes
from backend.services.drift import origin_routes
from backend.services.ais import routes as ais_routes
from backend.services.anomaly import routes as anomaly_routes
from backend.services.scoring import routes as scoring_routes
from backend.services.physics_verification import routes as physics_routes
from backend.services.ranking import routes as ranking_routes
from backend.services.reporting import routes as reporting_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slicktrace.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="SlickTrace v2 - Maritime Oil Spill Detection & Physics Origin Reconstruction Platform"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prototype accessibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers under /api
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)
app.include_router(spills.router, prefix=settings.API_V1_STR)
app.include_router(drift_routes.router, prefix=settings.API_V1_STR)
app.include_router(origin_routes.router, prefix=settings.API_V1_STR)
app.include_router(ais.router, prefix=settings.API_V1_STR)
app.include_router(ais_routes.router, prefix=settings.API_V1_STR)
app.include_router(anomaly_routes.router, prefix=settings.API_V1_STR)
app.include_router(scoring_routes.router, prefix=settings.API_V1_STR)
app.include_router(physics_routes.router, prefix=settings.API_V1_STR)
app.include_router(ranking_routes.router, prefix=settings.API_V1_STR)
app.include_router(suspects.router, prefix=settings.API_V1_STR)
app.include_router(verification.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(reporting_routes.router, prefix=settings.API_V1_STR)
app.include_router(satellite_routes.router, prefix=settings.API_V1_STR)
app.include_router(detection_routes.router, prefix=settings.API_V1_STR)
app.include_router(characterization_routes.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.PROJECT_NAME} backend server...")
    logger.info(f"DEMO_MODE active: {settings.DEMO_MODE}")
    init_db()

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "demo_mode": settings.DEMO_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
