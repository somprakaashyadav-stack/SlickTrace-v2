from fastapi import APIRouter
from typing import List
from backend.config import settings
from backend.demo_service import demo_service
from backend.schemas import (
    OilSpillObservationResponse,
    VesselMetadataResponse,
    AISVesselTrackFull,
    MetoceanFieldResponse
)

router = APIRouter(prefix="/demo", tags=["Demo Data Engine"])

@router.get("/status")
def get_demo_status():
    return {
        "demo_mode": settings.DEMO_MODE,
        "dataset": settings.DEMO_DATASET,
        "seed": 42,
        "description": "Deterministic synthetic dataset containing oil spill polygon, 8 vessel metadata profiles, high-density AIS tracks with transponder gaps and course deviations, and metocean wind/current fields."
    }

@router.post("/toggle")
def toggle_demo_mode(enabled: bool):
    settings.DEMO_MODE = enabled
    return {"demo_mode": settings.DEMO_MODE, "message": f"DEMO_MODE set to {settings.DEMO_MODE}"}

@router.get("/spill", response_model=OilSpillObservationResponse)
def get_demo_spill():
    """Returns synthetic oil spill observation data."""
    return demo_service.get_demo_spill()

@router.get("/vessels", response_model=List[VesselMetadataResponse])
def get_demo_vessels():
    """Returns metadata for 8 diverse vessels."""
    return demo_service.get_demo_vessels()

@router.get("/ais", response_model=List[AISVesselTrackFull])
def get_demo_ais():
    """Returns high-density AIS trajectories for all 8 vessels."""
    return demo_service.get_demo_ais_tracks()

@router.get("/metocean", response_model=MetoceanFieldResponse)
def get_demo_metocean():
    """Returns wind and ocean current vector fields around the spill region."""
    return demo_service.get_demo_metocean()
