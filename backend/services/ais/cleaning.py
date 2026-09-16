from typing import List, Dict, Any
from backend.services.ais.schemas import AisTrack, AisPoint
from backend.services.characterization.geometry import haversine_distance
from datetime import datetime

MAX_POSSIBLE_SPEED_KNOTS = 45.0
SUSPICIOUS_GAP_MINUTES = 60.0

def parse_time(iso_str: str) -> datetime:
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

def clean_ais_track(track: Dict[str, Any]) -> AisTrack:
    """
    Cleans raw AIS data by removing impossible coordinates and speed jumps.
    """
    cleaned_points: List[AisPoint] = []
    
    raw_points = sorted(track.get("path", []), key=lambda p: p.get("timestamp", ""))
    
    for i, pt in enumerate(raw_points):
        lat = pt.get("lat", pt.get("latitude", 0.0))
        lon = pt.get("lon", pt.get("longitude", 0.0))
        
        # 1. Remove impossible coordinates
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            continue
            
        new_pt = AisPoint(
            timestamp=pt.get("timestamp", ""),
            lat=lat,
            lon=lon,
            speed_knots=pt.get("speed_knots", 0.0),
            heading_deg=pt.get("heading_deg", 0.0),
            course_deg=pt.get("course_deg", 0.0),
            is_reconstructed=False
        )
        
        # 2. Remove impossible speed jumps (compare with last valid point)
        if len(cleaned_points) > 0:
            last_pt = cleaned_points[-1]
            try:
                dt_hours = (parse_time(new_pt.timestamp) - parse_time(last_pt.timestamp)).total_seconds() / 3600.0
                dist_nm = haversine_distance(last_pt.lon, last_pt.lat, new_pt.lon, new_pt.lat) / 1.852
                if dt_hours > 0:
                    implied_speed = dist_nm / dt_hours
                    if implied_speed > MAX_POSSIBLE_SPEED_KNOTS:
                        # Skip this point as it implies teleportation
                        continue
            except Exception:
                pass
                
        cleaned_points.append(new_pt)
        
    return AisTrack(
        mmsi=track.get("mmsi", 0),
        vessel_name=track.get("vessel_name", "Unknown"),
        vessel_type=track.get("vessel_type", "Unknown"),
        points=cleaned_points
    )

def identify_gaps(points: List[AisPoint]) -> List[int]:
    """
    Returns indices of points where the gap *after* it is suspicious.
    """
    suspicious_gap_indices = []
    for i in range(len(points) - 1):
        pt1 = points[i]
        pt2 = points[i+1]
        try:
            dt_minutes = (parse_time(pt2.timestamp) - parse_time(pt1.timestamp)).total_seconds() / 60.0
            if dt_minutes > SUSPICIOUS_GAP_MINUTES:
                suspicious_gap_indices.append(i)
        except Exception:
            pass
    return suspicious_gap_indices
