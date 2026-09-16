from backend.services.ais.schemas import AisTrack, CandidateScore, CandidateVessel
from backend.services.drift.schemas import OriginCandidate
from backend.services.characterization.geometry import haversine_distance
from backend.services.ais.cleaning import parse_time
import math

def score_vessel(track: AisTrack, origin: OriginCandidate) -> CandidateVessel:
    if not track.points:
        return CandidateVessel(
            mmsi=track.mmsi,
            vessel_name=track.vessel_name,
            vessel_type=track.vessel_type,
            scores=CandidateScore(),
            candidate_status="Irrelevant"
        )
        
    origin_t0 = parse_time(origin.T0)
    
    min_dist_km = float('inf')
    min_time_diff_hours = float('inf')
    reconstructed_count = 0
    time_near_origin = 0.0 # in hours
    
    last_pt = None
    
    for pt in track.points:
        if pt.is_reconstructed:
            reconstructed_count += 1
            
        try:
            pt_time = parse_time(pt.timestamp)
        except Exception:
            continue
            
        dist_km = haversine_distance(origin.X0, origin.Y0, pt.lon, pt.lat)
        min_dist_km = min(min_dist_km, dist_km)
        
        time_diff = abs((pt_time - origin_t0).total_seconds() / 3600.0)
        min_time_diff_hours = min(min_time_diff_hours, time_diff)
        
        if dist_km <= origin.uncertainty_radius_km:
            if last_pt:
                try:
                    last_time = parse_time(last_pt.timestamp)
                    dt_hours = abs((pt_time - last_time).total_seconds() / 3600.0)
                    time_near_origin += dt_hours
                except Exception:
                    pass
                    
        last_pt = pt
        
    # Spatial Score: 1.0 if inside uncertainty radius, decays outwards
    if min_dist_km <= origin.uncertainty_radius_km:
        spatial_score = 1.0
    else:
        # Decay factor
        excess_dist = min_dist_km - origin.uncertainty_radius_km
        spatial_score = max(0.0, math.exp(-excess_dist / 10.0))
        
    # Temporal Score: 1.0 if exactly at T0, decays over hours
    temporal_score = max(0.0, math.exp(-min_time_diff_hours / 4.0))
    
    # Trajectory Score: Higher if it spent time near the origin cone
    trajectory_score = min(1.0, time_near_origin / 2.0) if time_near_origin > 0 else (0.5 * spatial_score * temporal_score)
    
    # Reliability penalty for reconstructed points around the origin
    ais_reliability = 1.0
    if reconstructed_count > 0:
        ratio = reconstructed_count / len(track.points)
        ais_reliability = max(0.0, 1.0 - (ratio * 1.5))
        
    heading_score = 0.5 # Default placeholder unless we have drift direction
    
    # Total Score
    total = (
        (spatial_score * 0.35) + 
        (temporal_score * 0.30) + 
        (trajectory_score * 0.15) + 
        (ais_reliability * 0.10) + 
        (heading_score * 0.10)
    )
    
    status = "Low Risk"
    if total > 0.75:
        status = "High Risk"
    elif total > 0.4:
        status = "Medium Risk"
    elif total < 0.1:
        status = "Irrelevant"
        
    scores = CandidateScore(
        spatial_score=round(spatial_score, 3),
        temporal_score=round(temporal_score, 3),
        trajectory_score=round(trajectory_score, 3),
        heading_score=round(heading_score, 3),
        ais_reliability=round(ais_reliability, 3),
        total_score=round(total, 3)
    )
    
    return CandidateVessel(
        mmsi=track.mmsi,
        vessel_name=track.vessel_name,
        vessel_type=track.vessel_type,
        scores=scores,
        candidate_status=status,
        reconstructed_points=reconstructed_count
    )
