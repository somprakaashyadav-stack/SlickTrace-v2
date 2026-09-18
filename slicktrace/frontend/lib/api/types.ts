/**
 * SlickTrace v2 — Shared TypeScript types (mirror Pydantic schemas)
 */

export type UserRole = 'Investigator' | 'Analyst' | 'Administrator' | 'Investigator (Sandbox)'

export interface AuthUser {
  email: string
  role: UserRole
  full_name: string
  mode: 'real' | 'demo'
  authenticated: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  role: UserRole
  email: string
  full_name: string
  mode: 'real' | 'demo'
  expires_in: number
}

export type IncidentStatus = 'open' | 'in_progress' | 'review' | 'closed'
export type IncidentMode = 'real' | 'demo'
export type DetectionStatus = 'pending' | 'running' | 'done' | 'failed' | 'unavailable'
export type HindcastStatus = 'pending' | 'running' | 'done' | 'failed'

export interface Incident {
  id: string
  title: string
  description?: string
  operator: string
  status: IncidentStatus
  mode: IncidentMode
  created_at: string
  updated_at: string
}

export interface Imagery {
  id: string
  incident_id: string
  filename: string
  storage_key: string
  sha256: string
  size_bytes: number
  sensor?: string
  polarisation?: string
  scene_id?: string
  acquisition_time?: string
  content_type: string
  uploaded_at: string
}

export interface SatelliteEvidence {
  id: string
  incident_id: string
  filename: string
  storage_key: string
  file_hash: string
  size_bytes: number
  content_type: string
  platform?: string
  sensor?: string
  product_type?: string
  polarization?: string
  acquisition_time?: string
  temporal_attribution_available: boolean
  crs?: string
  crs_epsg?: number
  is_georeferenced: boolean
  geospatial_attribution_available: boolean
  resolution_x_m?: number
  resolution_y_m?: number
  width: number
  height: number
  bands: number
  nodata_value?: number
  dtype?: string
  analysis_ready_storage_key?: string
  processing_status: 'uploaded' | 'processing' | 'ready' | 'failed'
  validation_notes?: string[]
  raw_metadata?: Record<string, any>
  error_message?: string
  created_at: string
  updated_at: string
}

export interface SpillGeometry {
  id: string
  source_detection_id: string
  incident_id: string
  geojson_polygon: GeoJSONFeature | GeoJSONGeometry | Record<string, any>
  area_km2: number
  perimeter_km: number
  projected_crs: string
  centroid_lat: number
  centroid_lon: number
  bbox: [number, number, number, number]
  geometry_quality: {
    validity: string
    simplification_tolerance: number
    vertex_count: number
    components_count: number
    projected_crs_used: string
    pixel_fill_count?: number
  }
  created_at: string
}

export interface SpillDetection {
  id: string
  incident_id: string
  imagery_id: string
  status: DetectionStatus
  model_used?: string
  area_km2?: number
  confidence?: number
  lookalike_prob?: number
  is_oil?: boolean
  sam2_refined: boolean
  celery_task_id?: string
  error_message?: string
  unavailable_reason?: string
  created_at: string
  completed_at?: string
}

export interface HindcastRun {
  id: string
  incident_id: string
  detection_id: string
  status: HindcastStatus
  start_lat: number
  start_lon: number
  detection_time: string
  hours_back: number
  n_particles: number
  wind_reader?: string
  current_reader?: string
  origin_time_start?: string
  origin_time_end?: string
  origin_lat?: number
  origin_lon?: number
  origin_p50_polygon?: GeoJSONFeature | GeoJSONGeometry | Record<string, any>
  origin_p75_polygon?: GeoJSONFeature | GeoJSONGeometry | Record<string, any>
  origin_p90_polygon?: GeoJSONFeature | GeoJSONGeometry | Record<string, any>
  trajectory_geojson?: GeoJSONFeatureCollection
  particle_timesteps_geojson?: GeoJSONFeatureCollection
  uncertainty_metadata?: Record<string, unknown>
  duration_slices?: Record<string, {
    duration_hours: number
    origin_time: string
    centroid_lat: number
    centroid_lon: number
    spread_km: number
    p50_polygon?: any
    p75_polygon?: any
    p90_polygon?: any
    probability_surface?: any
  }>
  simulation_config?: Record<string, unknown>
  forcing_provenance?: Record<string, unknown>
  celery_task_id?: string
  error_message?: string
  created_at: string
  completed_at?: string
}

export interface CandidateVessel {
  id: string
  incident_id: string
  mmsi: string
  vessel_name?: string
  vessel_type?: string
  flag_state?: string
  imo_number?: string
  physical_score?: number
  rank?: number
  proximity_score?: number
  timing_score?: number
  heading_score?: number
  speed_anomaly_score?: number
  ais_gap_score?: number
  vessel_type_score?: number
  anomalies?: string[]
  isolation_forest_score?: number
  closest_approach_km?: number
  closest_approach_time?: string
  counterfactual_run: boolean
  counterfactual_consistent?: boolean
  counterfactual_notes?: string
  created_at: string
}

export interface EvidenceArtifact {
  artifact_id: string
  artifact_type: string
  sha256: string
  size_bytes: number
  storage_key: string
  description: string
  metadata: Record<string, unknown>
  recorded_at: string
}

export interface EvidenceManifest {
  manifest_id: string
  incident_id: string
  created_at: string
  exported_at: string
  artifact_count: number
  artifacts: EvidenceArtifact[]
  manifest_sha256: string
}

// GeoJSON types
export interface GeoJSONFeature {
  type: 'Feature'
  geometry: GeoJSONGeometry | null
  properties: Record<string, unknown>
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
}

export type GeoJSONGeometry =
  | { type: 'Point'; coordinates: [number, number] }
  | { type: 'LineString'; coordinates: [number, number][] }
  | { type: 'Polygon'; coordinates: [number, number][][] }
  | { type: 'MultiPolygon'; coordinates: [number, number][][][] }
