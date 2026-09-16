from fastapi import APIRouter
from typing import List
from backend.demo_service import demo_service
from backend.schemas import AISVesselTrack

router = APIRouter(prefix="/ais", tags=["AIS Correlation"])

@router.get("/tracks", response_model=List[AISVesselTrack])
def get_ais_tracks():
    return demo_service.get_ais_vessels()
