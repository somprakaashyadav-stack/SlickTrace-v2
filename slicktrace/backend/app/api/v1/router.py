"""
SlickTrace v2 — API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    incidents,
    imagery,
    satellite_evidence,
    copernicus,
    detection,
    detection_pipeline,
    hindcast,
    ais,
    candidates,
    evidence,
    websocket,
    ocean_forcing,
    auth,
    datasets,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(imagery.router, prefix="/incidents", tags=["imagery"])
api_router.include_router(satellite_evidence.router, prefix="/incidents", tags=["satellite-evidence"])
api_router.include_router(copernicus.router, prefix="/copernicus", tags=["copernicus"])
api_router.include_router(detection_pipeline.router, prefix="/detection", tags=["detection-pipeline"])
api_router.include_router(detection.router, prefix="/incidents", tags=["detection"])
api_router.include_router(hindcast.router, prefix="/incidents", tags=["hindcast"])
api_router.include_router(ocean_forcing.router, prefix="/ocean", tags=["ocean-forcing"])
api_router.include_router(ais.router, prefix="/incidents", tags=["ais"])
api_router.include_router(candidates.router, prefix="/incidents", tags=["candidates"])
api_router.include_router(evidence.router, prefix="/incidents", tags=["evidence"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
