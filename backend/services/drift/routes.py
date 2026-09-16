from fastapi import APIRouter, HTTPException
from backend.services.drift.schemas import DriftSimulationRequest, DriftSimulationResponse
from backend.services.drift.origin import generate_origin_candidate
from backend.services.drift.physics_engine import get_physics_engine
from backend.demo_service import demo_service
from backend.services.providers.factory import metocean_provider
from backend.config import settings
from datetime import datetime

router = APIRouter(prefix="/drift", tags=["Hydrodynamic Drift Modeling"])

@router.post("/simulate", response_model=DriftSimulationResponse)
def run_drift_simulation(request: DriftSimulationRequest):
    """
    Executes a backward hindcast or forward forecast simulation.
    Uses 'Demo Lagrangian Model' or 'OpenDrift' based on DRIFT_ENGINE config.
    """
    # 1. Fetch the detected spill metadata for origin (centroid and timestamp)
    spill = demo_service.get_demo_spill()
    if spill.get("spill_id") != request.spill_id and settings.DEMO_MODE:
        # Just use demo spill data for any ID in demo mode
        pass
        
    start_lat = spill.get("latitude", 18.91)
    start_lon = spill.get("longitude", 72.35)
    start_time_str = spill.get("timestamp", "2026-09-12T14:30:00Z")
    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
    
    # 2. Fetch Environmental Conditions
    try:
        met = metocean_provider.get_wind_and_currents(start_lat, start_lon, start_time_str)
        wind_knots = met.get("wind_speed_knots", 14.2)
        wind_dir = met.get("wind_dir_deg", 210.0)
        curr_knots = met.get("current_speed_knots", 1.4)
        curr_dir = met.get("current_dir_deg", 245.0)
    except Exception:
        # Fallback to demo service structure
        met = demo_service.get_demo_metocean()
        wind_knots = met.get("wind", {}).get("speed_knots", 14.2)
        wind_dir = met.get("wind", {}).get("direction_deg", 210.0)
        curr_knots = met.get("current", {}).get("speed_knots", 1.4)
        curr_dir = met.get("current", {}).get("direction_deg", 245.0)
    
    # 3. Determine Engine
    engine = get_physics_engine()
    engine_name = engine.__class__.__name__
            
    # 4. Run Physics
    candidate = None
    
    # Propagate
    trajectories = engine.run_simulation(
        start_lat=start_lat,
        start_lon=start_lon,
        start_time=start_time,
        hours=request.hours_modeled,
        reverse=(request.mode == "backward"),
        num_particles=50,
        wind_knots=wind_knots,
        wind_dir=wind_dir,
        current_knots=curr_knots,
        current_dir=curr_dir
    )
    
    # Calculate End Centroid
    if trajectories:
        final_lats = [t[-1]["lat"] for t in trajectories]
        final_lons = [t[-1]["lon"] for t in trajectories]
        end_lat = sum(final_lats) / len(final_lats)
        end_lon = sum(final_lons) / len(final_lons)
    else:
        end_lat, end_lon = start_lat, start_lon
    
    if request.mode == "backward":
        candidate = generate_origin_candidate(end_lat, end_lon, start_time_str, request.hours_modeled, trajectories)

    # 5. Build Response
    return DriftSimulationResponse(
        slick_id=request.spill_id,
        engine=engine_name,
        direction=request.mode,
        hours_modeled=request.hours_modeled,
        particle_count=len(trajectories),
        wind_speed_knots=wind_knots,
        wind_direction_deg=wind_dir,
        current_speed_knots=curr_knots,
        current_direction_deg=curr_dir,
        trajectories=trajectories,
        origin_candidate=candidate
    )
