from typing import List
from datetime import datetime, timedelta
import uuid
import random
from backend.services.ais.schemas import AisTrack
from backend.services.physics_verification.schemas import PhysicsScenario
from backend.services.ais.cleaning import parse_time

def generate_candidate_scenarios(track: AisTrack, estimated_t0: str, hours_range: float = 6.0) -> List[PhysicsScenario]:
    """
    Generates multiple counterfactual scenarios for a given candidate vessel based on its track.
    We isolate the segment of the track near the estimated T0.
    """
    scenarios = []
    t0_dt = parse_time(estimated_t0)
    
    # Define acceptable time window
    window_start = t0_dt - timedelta(hours=hours_range)
    window_end = t0_dt + timedelta(hours=hours_range)
    
    valid_points = []
    for pt in track.points:
        try:
            pt_time = parse_time(pt.timestamp)
            if window_start <= pt_time <= window_end:
                valid_points.append((pt, pt_time))
        except:
            continue
            
    if not valid_points:
        return []
        
    # We will sample up to 5 scenarios from the valid points along the track
    # varying the exact release time and introducing minor environmental perturbations
    
    # Sort by time
    valid_points.sort(key=lambda x: x[1])
    
    # Downsample if too many
    if len(valid_points) > 5:
        step = max(1, len(valid_points) // 5)
        sampled_points = valid_points[::step][:5]
    else:
        sampled_points = valid_points
        
    for pt, pt_time in sampled_points:
        # Calculate how long the slick would drift from this release time to NOW (assumed as detection time)
        # For the demo, we assume the detection time is the latest timestamp in the track or similar.
        # But for simplification, we just say duration is time from release to current analysis time.
        # Let's say analysis time is T0 + 24h as a rough demo constant, or we can use fixed 24h.
        
        # Let's add a baseline scenario
        scenarios.append(PhysicsScenario(
            scenario_id=str(uuid.uuid4())[:8],
            release_time=pt_time.isoformat(),
            release_lat=pt.lat,
            release_lon=pt.lon,
            duration_hours=24.0, # Will be adjusted by simulator if needed
            wind_variance=0.0,
            current_variance=0.0
        ))
        
        # Add a perturbed environment scenario for the point closest to actual T0
        time_diff = abs((pt_time - t0_dt).total_seconds())
        if time_diff < 3600: # Within 1 hour of estimated T0
            scenarios.append(PhysicsScenario(
                scenario_id=str(uuid.uuid4())[:8],
                release_time=pt_time.isoformat(),
                release_lat=pt.lat + random.uniform(-0.01, 0.01),
                release_lon=pt.lon + random.uniform(-0.01, 0.01),
                duration_hours=24.0,
                wind_variance=1.5,
                current_variance=0.1
            ))
            
    return scenarios
