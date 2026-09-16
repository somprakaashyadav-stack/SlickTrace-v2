from datetime import datetime
from typing import List, Dict, Any, Tuple
from backend.services.drift.particles import DemoLagrangianModel

def run_hindcast(
    start_lat: float, 
    start_lon: float, 
    start_time: datetime, 
    hours: int, 
    wind_speed: float, 
    wind_dir: float, 
    curr_speed: float, 
    curr_dir: float
) -> Tuple[List[List[Dict[str, Any]]], float, float]:
    """
    Runs backward simulation (hindcasting) to find origin candidate points.
    Returns: trajectories, origin_lat, origin_lon
    """
    model = DemoLagrangianModel(
        wind_speed_knots=wind_speed,
        wind_dir_deg=wind_dir,
        current_speed_knots=curr_speed,
        current_dir_deg=curr_dir
    )
    
    # Generate 50 particles for the demo
    trajectories = model.propagate(
        start_lat=start_lat,
        start_lon=start_lon,
        start_time=start_time,
        hours=hours,
        reverse=True,
        num_particles=50
    )
    
    # Calculate the centroid of the final particle positions (the estimated origin)
    final_lats = [t[-1]["lat"] for t in trajectories]
    final_lons = [t[-1]["lon"] for t in trajectories]
    
    origin_lat = sum(final_lats) / len(final_lats)
    origin_lon = sum(final_lons) / len(final_lons)
    
    return trajectories, origin_lat, origin_lon
