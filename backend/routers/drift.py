from fastapi import APIRouter
from backend.demo_service import demo_service
from backend.schemas import DriftSimulationResponse

router = APIRouter(prefix="/drift", tags=["Drift"])

@router.get("/simulation", response_model=DriftSimulationResponse)
def get_drift_simulation():
    return demo_service.get_drift_simulation()
