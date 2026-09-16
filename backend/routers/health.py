from fastapi import APIRouter
from backend.config import settings
from backend.schemas import SystemHealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=SystemHealthResponse)
def get_health_status():
    db_type = "SQLite (Fallback)" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL + PostGIS"
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": "2.0.0",
        "demo_mode": settings.DEMO_MODE,
        "database_type": db_type,
        "active_dataset": settings.DEMO_DATASET,
        "modules_ready": [
            "ingestion", "preprocessing", "detection", "characterization",
            "drift", "origin", "ais", "anomaly", "scoring", "physics_verification", "reporting"
        ]
    }
