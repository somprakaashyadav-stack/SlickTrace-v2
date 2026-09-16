import axios from 'axios';
import {
  SystemHealth,
  SatelliteProcessResponse,
  SatelliteStatusResponse,
  DetectionResultResponse,
  OilSpillObservation,
  VesselMetadata,
  AISVesselTrackFull,
  MetoceanField,
  SpillSummary,
  DriftSimulation,
  AISVesselTrack,
  CandidatePriority,
  InitialScoreResponse,
  PhysicsVerificationResponse,
  FinalRankingResponse,
  EvidenceReport,
  SlickProfile,
  OriginConeResponse
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api';

export const api = {
  getHealth: async (): Promise<SystemHealth> => {
    const res = await axios.get<SystemHealth>(`${API_BASE}/health`);
    return res.data;
  },

  getDemoStatus: async () => {
    const res = await axios.get(`${API_BASE}/demo/status`);
    return res.data;
  },

  // --- AI DETECTION MODULE ENDPOINTS ---

  runDetection: async (
    model_architecture: string = "U-Net",
    scene_id: string = "S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI"
  ): Promise<DetectionResultResponse> => {
    const res = await axios.post<DetectionResultResponse>(`${API_BASE}/detection/run`, {
      scene_id,
      model_architecture,
      confidence_threshold: 0.85
    });
    return res.data;
  },

  getDetectionResult: async (spill_id: string): Promise<DetectionResultResponse> => {
    const res = await axios.get<DetectionResultResponse>(`${API_BASE}/detection/result/${spill_id}`);
    return res.data;
  },

  // --- CHARACTERIZATION MODULE ENDPOINTS ---

  runCharacterization: async (spill_id: string): Promise<SlickProfile> => {
    const res = await axios.post<SlickProfile>(`${API_BASE}/characterization/${spill_id}`);
    return res.data;
  },

  getCharacterization: async (spill_id: string): Promise<SlickProfile> => {
    const res = await axios.get<SlickProfile>(`${API_BASE}/characterization/${spill_id}`);
    return res.data;
  },


  // --- SATELLITE MODULE ENDPOINTS ---

  getSatelliteStatus: async (): Promise<SatelliteStatusResponse> => {
    const res = await axios.get<SatelliteStatusResponse>(`${API_BASE}/satellite/status`);
    return res.data;
  },

  processSatelliteScene: async (
    scene_id: string = "S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI",
    satellite: string = "Sentinel-1B",
    filter_type: string = "Lee (5x5)"
  ): Promise<SatelliteProcessResponse> => {
    const res = await axios.post<SatelliteProcessResponse>(`${API_BASE}/satellite/process`, {
      scene_id,
      satellite,
      filter_type
    });
    return res.data;
  },

  // --- DEMO DATA ENGINE ENDPOINTS ---

  getDemoSpill: async (): Promise<OilSpillObservation> => {
    const res = await axios.get<OilSpillObservation>(`${API_BASE}/demo/spill`);
    return res.data;
  },

  getDemoVessels: async (): Promise<VesselMetadata[]> => {
    const res = await axios.get<VesselMetadata[]>(`${API_BASE}/demo/vessels`);
    return res.data;
  },

  getDemoAIS: async (): Promise<AISVesselTrackFull[]> => {
    const res = await axios.get<AISVesselTrackFull[]>(`${API_BASE}/demo/ais`);
    return res.data;
  },

  getDemoMetocean: async (): Promise<MetoceanField> => {
    const res = await axios.get<MetoceanField>(`${API_BASE}/demo/metocean`);
    return res.data;
  },

  // --- PLATFORM ENDPOINTS ---

  getSpillSummary: async (): Promise<SpillSummary> => {
    const res = await axios.get<SpillSummary>(`${API_BASE}/spills/current`);
    return res.data;
  },

  runDriftSimulation: async (spill_id: string, hours: number, mode: string = "backward"): Promise<DriftSimulation> => {
    const res = await axios.post<DriftSimulation>(`${API_BASE}/drift/simulate`, {
      spill_id,
      hours_modeled: hours,
      mode
    });
    return res.data;
  },

  getOriginCone: async (spill_id: string): Promise<OriginConeResponse> => {
    const res = await axios.get<OriginConeResponse>(`${API_BASE}/origin/${spill_id}`);
    return res.data;
  },

  getAISTracks: async (): Promise<AISVesselTrack[]> => {
    const res = await axios.get<AISVesselTrack[]>(`${API_BASE}/ais/tracks`);
    return res.data;
  },

  getInitialScoring: async (spill_id: string): Promise<InitialScoreResponse> => {
    const res = await axios.post<InitialScoreResponse>(`${API_BASE}/scoring/initial/${spill_id}`);
    return res.data;
  },

  getPhysicsVerification: async (spill_id: string): Promise<PhysicsVerificationResponse> => {
    const res = await axios.post<PhysicsVerificationResponse>(`${API_BASE}/physics_verification/run/${spill_id}`);
    return res.data;
  },

  getFinalRanking: async (spill_id: string): Promise<FinalRankingResponse> => {
    const res = await axios.get<FinalRankingResponse>(`${API_BASE}/ranking/${spill_id}`);
    return res.data;
  },

  getEvidenceReport: async (): Promise<EvidenceReport> => {
    const res = await axios.get<EvidenceReport>(`${API_BASE}/reports/dossier`);
    return res.data;
  }
};
