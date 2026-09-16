from fastapi import APIRouter
from typing import List
from backend.demo_service import demo_service
from backend.schemas import SuspectVesselScore

router = APIRouter(prefix="/suspects", tags=["Suspect Ranking"])

@router.get("/rankings", response_model=List[SuspectVesselScore])
def get_suspect_rankings():
    return demo_service.get_suspect_rankings()
