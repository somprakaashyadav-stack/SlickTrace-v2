from fastapi import APIRouter
from backend.demo_service import demo_service
from backend.schemas import SpillDetectionSummary

router = APIRouter(prefix="/spills", tags=["Spills"])

@router.get("/current", response_model=SpillDetectionSummary)
def get_current_spill():
    return demo_service.get_spill_summary()
