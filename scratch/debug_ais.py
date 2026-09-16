import os
from backend.services.drift.origin_routes import get_origin_cone
from backend.demo_service import demo_service
from backend.services.ais.cleaning import clean_ais_track
from backend.services.ais.filtering import apply_space_time_window
from backend.services.ais.correlation import score_vessel

origin_cone = get_origin_cone("test-spill-id")
origin = origin_cone.probable_origin

print(f"Origin Cone T0: {origin.T0}, X0: {origin.X0}, Y0: {origin.Y0}, radius: {origin.uncertainty_radius_km}")

raw_tracks = demo_service.get_demo_ais_tracks()
for raw in raw_tracks:
    cleaned = clean_ais_track(raw)
    print(f"Vessel {raw.get('mmsi')} - Raw points: {len(raw.get('path', []))} -> Cleaned: {len(cleaned.points)}")
    if len(cleaned.points) > 0:
        print(f"  First point: {cleaned.points[0]}")
    
    in_window = apply_space_time_window(cleaned, origin)
    print(f"  In window: {in_window}")
    if in_window:
        candidate = score_vessel(cleaned, origin)
        print(f"  Status: {candidate.candidate_status} - Score: {candidate.scores.total_score}")
