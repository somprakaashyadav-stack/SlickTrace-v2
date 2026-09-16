from fastapi import APIRouter
from backend.services.drift.schemas import OriginConeResponse, DriftSimulationRequest
from backend.services.drift.routes import run_drift_simulation
from backend.demo_service import demo_service

router = APIRouter(prefix="/origin", tags=["4D Origin Cone"])

@router.get("/{spill_id}", response_model=OriginConeResponse)
def get_origin_cone(spill_id: str):
    """
    Returns the 4D Origin Cone including observed location, time window, uncertainty,
    probable origin centroid, and backward trajectories.
    """
    spill = demo_service.get_demo_spill()
    
    # Run the backward drift simulation for 12 hours to match demo data
    sim_request = DriftSimulationRequest(spill_id=spill_id, hours_modeled=12, mode="backward")
    sim_response = run_drift_simulation(sim_request)
    
    return OriginConeResponse(
        spill_id=spill_id,
        observed_slick_polygon=spill.get("polygon", []),
        observed_centroid=[spill.get("longitude", 0.0), spill.get("latitude", 0.0)],
        time_window_start=sim_response.origin_candidate.T0 if sim_response.origin_candidate else "",
        time_window_end=spill.get("timestamp", ""),
        probable_origin=sim_response.origin_candidate,
        trajectories=sim_response.trajectories
    )
