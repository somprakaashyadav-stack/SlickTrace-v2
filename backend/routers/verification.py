from fastapi import APIRouter
from backend.demo_service import demo_service
from backend.schemas import PhysicsVerificationResponse

router = APIRouter(prefix="/verification", tags=["Physics Verification"])

@router.get("/status", response_model=PhysicsVerificationResponse)
def get_verification_status():
    return demo_service.get_physics_verification()
