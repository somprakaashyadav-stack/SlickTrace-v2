export interface SystemHealth {
  status: string;
  project: string;
  version: string;
  demo_mode: boolean;
  database_type: string;
  active_dataset: string;
  modules_ready: string[];
}

export interface LookalikeCheckDetail {
  check_name: string;
  passed: boolean;
  risk_score: number;
  reason: string;
}

export interface DetectionResultResponse {
  spill_id: string;
  scene_id: string;
  model_name: string;
  inference_mode: string;
  detection_confidence: number;
  segmentation_status: string;
  slick_area_km2: number;
  slick_perimeter_km: number;
  slick_polygon: number[][];
  lookalike_checks: LookalikeCheckDetail[];
  candidate_mask_count: number;
  stats?: Record<string, any>;
}

export interface PreprocessingStepDetail {
  step_name: string;
  status: string;
  method: string;
  is_placeholder: boolean;
  description: string;
}

export interface SatelliteProcessResponse {
  scene_id: string;
  satellite: string;
  sensor: string;
  acquisition_time: string;
  polarization: string;
  processing_status: string;
  image_dimensions: number[];
  preprocessing_steps: PreprocessingStepDetail[];
  output_path_reference: string;
  stats: {
    raw_mean?: number;
    filtered_mean?: number;
    db_range_min?: number;
    db_range_max?: number;
    dark_spot_attenuation_db?: number;
  };
}

export interface SatelliteStatusResponse {
  service_status: string;
  copernicus_api_ready: boolean;
  demo_mode: boolean;
  available_demo_granules: Record<string, any>[];
}

export interface OilSpillObservation {
  spill_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  area_km2: number;
  perimeter_km: number;
  length_km: number;
  orientation_deg: number;
  confidence: number;
  polygon: number[][];
}

export interface VesselMetadata {
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  length: number;
  flag: string;
  operational_capability: string;
  category?: string;
}

export interface AISTrackPointDetail {
  timestamp: string;
  latitude: number;
  longitude: number;
  speed_knots: number;
  heading_deg: number;
  course_deg: number;
}

export interface AISVesselTrackFull {
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  has_ais_gap: boolean;
  gap_duration_mins: number;
  has_course_deviation: boolean;
  physical_inconsistency: boolean;
  path: AISTrackPointDetail[];
}

export interface MetoceanVectorPoint {
  latitude: number;
  longitude: number;
  wind_speed_knots: number;
  wind_direction_deg: number;
  current_speed_knots: number;
  current_direction_deg: number;
}

export interface MetoceanField {
  region: string;
  timestamp: string;
  wind: {
    speed_knots: number;
    direction_deg: number;
    u_ms?: number;
    v_ms?: number;
  };
  current: {
    speed_knots: number;
    direction_deg: number;
    u_ms?: number;
    v_ms?: number;
  };
  wave_height_m: number;
  sea_surface_temp_c: number;
  vector_grid: MetoceanVectorPoint[];
}

export interface SpillSummary {
  slick_id: string;
  scene_id: string;
  satellite: string;
  detection_time: string;
  center_lat: number;
  center_lon: number;
  area_sq_km: number;
  estimated_volume_m3: number;
  confidence_score: number;
  thick_spot_ratio: number;
  polygon: number[][];
}

export interface DriftTrajectoryPoint {
  step: number;
  time: string;
  lat: number;
  lon: number;
}

export interface OriginCandidate {
  X0: number;
  Y0: number;
  T0: string;
  delta_t_hours: number;
  uncertainty_radius_km: number;
  origin_probability: number;
}

export interface OriginEllipse {
  center_lat: number;
  center_lon: number;
  major_axis_km: number;
  minor_axis_km: number;
  orientation_deg: number;
  estimated_release_time: string;
}


export interface DriftSimulation {
  slick_id: string;
  direction: string;
  hours_modeled: number;
  particle_count: number;
  wind_speed_knots: number;
  wind_direction_deg: number;
  current_speed_knots: number;
  current_direction_deg: number;
  engine: string;
  trajectories: DriftTrajectoryPoint[][];
  origin_candidate?: OriginCandidate;
}

export interface OriginConeResponse {
  spill_id: string;
  observed_slick_polygon: number[][];
  observed_centroid: number[];
  time_window_start: string;
  time_window_end: string;
  probable_origin: OriginCandidate;
  trajectories: DriftTrajectoryPoint[][];
}


export interface AISTrackPoint {
  timestamp: string;
  lat: number;
  lon: number;
  speed_knots: number;
  course_deg: number;
  heading_deg: number;
}

export interface AISVesselTrack {
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  flag: string;
  imo?: number;
  closest_distance_km: number;
  time_of_closest_approach: string;
  path: AISTrackPoint[];
}

export interface SuspectVesselScore {
  rank: number;
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  flag: string;
  composite_score: number;
  spatial_score: number;
  temporal_score: number;
  anomaly_score: number;
  discharge_risk_score: number;
  risk_level: string;
  ais_gap_detected: boolean;
  ais_gap_duration_mins: number;
}

export interface CandidatePriority {
  rank: number;
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  initial_score: number;
  spatial_score: number;
  temporal_score: number;
  trajectory_score: number;
  behavior_score: number;
  ais_score: number;
  capability_score: number;
  positive_evidence: string[];
  negative_evidence: string[];
}

export interface InitialScoreResponse {
  spill_id: string;
  candidates: CandidatePriority[];
}


export interface PhysicsScenario {
  scenario_id: string;
  release_time: string;
  release_lat: number;
  release_lon: number;
  duration_hours: number;
  wind_variance: number;
  current_variance: number;
}

export interface PhysicsMetrics {
  spatial_overlap_pct: number;
  centroid_error_km: number;
  shape_similarity_score: number;
  orientation_similarity_score: number;
  timing_error_hours: number;
}

export interface PhysicsVerificationResult {
  mmsi: number;
  vessel_name: string;
  physics_consistency_score: number;
  classification: string;
  best_scenario: PhysicsScenario;
  metrics: PhysicsMetrics;
}

export interface PhysicsVerificationResponse {
  spill_id: string;
  top_n_tested: number;
  results: PhysicsVerificationResult[];
}

export interface FinalCandidateRanking {
  rank: number;
  vessel_name: string;
  mmsi: number;
  vessel_type: string;
  initial_score: number;
  physics_score: number;
  final_score: number;
  rank_change: number;
  evidence_for: string[];
  evidence_against: string[];
  ais_reliability: string;
  investigation_priority: string;
  rank_change_explanation: string;
}

export interface FinalRankingResponse {
  spill_id: string;
  alpha_weight: number;
  beta_weight: number;
  rankings: FinalCandidateRanking[];
}

export interface EvidenceReport {
  incident_id: string;
  dossier_reference: string;
  generated_at: string;
  spill_summary: SpillSummary;
  prime_suspect: CandidatePriority;
  drift_physics_summary: OriginEllipse;
  verification_status: string;
  download_urls: {
    json: string;
    pdf: string;
  };
}

export type ViewType =
  | 'dashboard'
  | 'detection'
  | 'drift'
  | 'ais'
  | 'suspects'
  | 'verification'
  | 'report';

export interface SlickProfile {
  spill_id: string;
  centroid: number[];
  area_km2: number;
  perimeter_km: number;
  length_km: number;
  width_km: number;
  orientation_deg: number;
  elongation_ratio: number;
  fragmentation_index: number;
  estimated_age_hours: number;
  age_confidence: number;
  bounding_box: number[][];
  age_indicators_used: string[];
}

