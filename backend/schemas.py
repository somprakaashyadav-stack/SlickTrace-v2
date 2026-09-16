from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SystemHealthResponse(BaseModel):
    status: str
    project: str
    version: str
    demo_mode: bool
    database_type: str
    active_dataset: str
    modules_ready: List[str]

class GeoCoordinates(BaseModel):
    lat: float
    lon: float

# --- DEMO ENGINE SCHEMAS ---

class OilSpillObservationResponse(BaseModel):
    spill_id: str
    timestamp: str
    latitude: float
    longitude: float
    area_km2: float
    perimeter_km: float
    length_km: float
    orientation_deg: float
    confidence: float
    polygon: List[List[float]]

class VesselMetadataResponse(BaseModel):
    mmsi: int
    vessel_name: str
    vessel_type: str
    length: float
    flag: str
    operational_capability: str
    category: Optional[str] = None

class AISTrackPointDetail(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    speed_knots: float
    heading_deg: float
    course_deg: float

class AISVesselTrackFull(BaseModel):
    mmsi: int
    vessel_name: str
    vessel_type: str
    has_ais_gap: bool = False
    gap_duration_mins: int = 0
    has_course_deviation: bool = False
    physical_inconsistency: bool = False
    path: List[AISTrackPointDetail]

class MetoceanVectorPoint(BaseModel):
    latitude: float
    longitude: float
    wind_speed_knots: float
    wind_direction_deg: float
    current_speed_knots: float
    current_direction_deg: float

class MetoceanFieldResponse(BaseModel):
    region: str
    timestamp: str
    wind: Dict[str, Any]
    current: Dict[str, Any]
    wave_height_m: float
    sea_surface_temp_c: float
    vector_grid: List[MetoceanVectorPoint]

# --- PLATFORM SCHEMAS ---

class SpillDetectionSummary(BaseModel):
    slick_id: str
    scene_id: str
    satellite: str
    detection_time: str
    center_lat: float
    center_lon: float
    area_sq_km: float
    estimated_volume_m3: float
    confidence_score: float
    thick_spot_ratio: float
    polygon: List[List[float]]

class DriftParticle(BaseModel):
    particle_id: int
    lat: float
    lon: float
    timestamp: str
    depth_m: float = 0.0

class DriftSimulationResponse(BaseModel):
    slick_id: str
    direction: str
    hours_modeled: int
    particle_count: int
    wind_speed_knots: float
    wind_direction_deg: float
    current_speed_knots: float
    current_direction_deg: float
    trajectories: List[List[Dict[str, Any]]]
    origin_ellipse: Dict[str, Any]

class AISTrackPoint(BaseModel):
    timestamp: str
    lat: float
    lon: float
    speed_knots: float
    course_deg: float
    heading_deg: float

class AISVesselTrack(BaseModel):
    mmsi: int
    vessel_name: str
    vessel_type: str
    flag: str
    imo: Optional[int] = None
    closest_distance_km: float
    time_of_closest_approach: str
    path: List[AISTrackPoint]

class SuspectVesselScore(BaseModel):
    rank: int
    mmsi: int
    vessel_name: str
    vessel_type: str
    flag: str
    composite_score: float
    spatial_score: float
    temporal_score: float
    anomaly_score: float
    discharge_risk_score: float
    risk_level: str
    ais_gap_detected: bool
    ais_gap_duration_mins: int
    speed_anomaly: str

class PhysicsVerificationResponse(BaseModel):
    vessel_mmsi: int
    vessel_name: str
    forward_simulation_match_index: float
    mean_spatial_error_km: float
    hydrodynamic_confidence: float
    verification_status: str
    comparison_particles: List[Dict[str, Any]]

class EvidenceReportResponse(BaseModel):
    incident_id: str
    dossier_reference: str
    generated_at: str
    spill_summary: Dict[str, Any]
    prime_suspect: Dict[str, Any]
    drift_physics_summary: Dict[str, Any]
    verification_status: str
    download_urls: Dict[str, str]
