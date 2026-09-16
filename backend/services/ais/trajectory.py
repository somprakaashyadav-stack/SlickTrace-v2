from backend.services.ais.schemas import AisTrack, AisPoint
from backend.services.ais.cleaning import identify_gaps, parse_time
from datetime import timedelta
import copy

INTERPOLATION_STEP_MINUTES = 15.0

def reconstruct_trajectory(track: AisTrack) -> AisTrack:
    """
    Identifies suspicious gaps and performs a linear kinematic interpolation 
    (constant velocity approximation) to fill in missing points.
    Flags interpolated points with is_reconstructed=True.
    """
    if len(track.points) < 2:
        return track
        
    gaps = identify_gaps(track.points)
    if not gaps:
        return track
        
    new_points = []
    
    for i in range(len(track.points) - 1):
        pt1 = track.points[i]
        pt2 = track.points[i+1]
        
        new_points.append(pt1)
        
        if i in gaps:
            t1 = parse_time(pt1.timestamp)
            t2 = parse_time(pt2.timestamp)
            total_seconds = (t2 - t1).total_seconds()
            
            steps = int(total_seconds / (INTERPOLATION_STEP_MINUTES * 60))
            if steps > 1:
                lat_step = (pt2.lat - pt1.lat) / steps
                lon_step = (pt2.lon - pt1.lon) / steps
                
                for step_idx in range(1, steps):
                    interp_time = t1 + timedelta(seconds=step_idx * (INTERPOLATION_STEP_MINUTES * 60))
                    
                    interp_pt = AisPoint(
                        timestamp=interp_time.isoformat().replace("+00:00", "Z"),
                        lat=pt1.lat + lat_step * step_idx,
                        lon=pt1.lon + lon_step * step_idx,
                        speed_knots=pt1.speed_knots, # Simplified constant speed
                        heading_deg=pt1.heading_deg,
                        course_deg=pt1.course_deg,
                        is_reconstructed=True
                    )
                    new_points.append(interp_pt)
                    
    new_points.append(track.points[-1])
    
    reconstructed_track = copy.deepcopy(track)
    reconstructed_track.points = new_points
    return reconstructed_track
