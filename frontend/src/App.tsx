import React, { useState, useEffect, Component, ErrorInfo, ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { api } from './services/api';
import { TopBar } from './components/TopBar';
import { HorizontalNav } from './components/HorizontalNav';
import { Incident, MetoceanData, DEMO_INCIDENTS, DEMO_METOCEAN } from './types/app';
import {
  SpillSummary,
  DriftSimulation,
  AISVesselTrack,
  PhysicsVerificationResponse,
  FinalRankingResponse,
  CandidatePriority
} from './types';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { DriftBacktrackingPage } from './pages/DriftBacktrackingPage';
import { VesselAttributionPage } from './pages/VesselAttributionPage';
import { EvidenceCenterPage } from './pages/EvidenceCenterPage';
import { SatelliteStudioPage } from './pages/SatelliteStudioPage';
import { SpillAnalyticsPage } from './pages/SpillAnalyticsPage';
import { SARDetectionLabPage } from './pages/SARDetectionLabPage';

// ── Error Boundary ──────────────────────────────────────────────────────────
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('SlickTrace crash:', error, info); }
  render() {
    if (this.state.error) {
      return (
        <div className="flex h-screen w-screen bg-[#070B12] text-[#F8FAFC] items-center justify-center font-mono p-8">
          <div className="max-w-xl w-full border border-red-500/40 rounded-lg p-6 bg-red-950/20 space-y-4">
            <h1 className="text-[#EF4444] text-lg font-bold tracking-widest">⚠ SYSTEM ERROR</h1>
            <p className="text-slate-300 text-sm">{this.state.error.message}</p>
            <pre className="text-xs text-slate-500 overflow-auto max-h-48">{this.state.error.stack}</pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-[#0284C7] hover:bg-sky-500 text-white rounded text-sm"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── App ─────────────────────────────────────────────────────────────────────
export const App: React.FC = () => {
  // Data State
  const [spill, setSpill] = useState<SpillSummary>();
  const [drift, setDrift] = useState<DriftSimulation>();
  const [vessels, setVessels] = useState<AISVesselTrack[]>([]);
  const [physics, setPhysics] = useState<PhysicsVerificationResponse>();
  const [ranking, setRanking] = useState<FinalRankingResponse>();
  const [loading, setLoading] = useState<boolean>(true);

  // App State
  const [activeIncident, setActiveIncident] = useState<Incident>(DEMO_INCIDENTS[0]);
  const [metocean, setMetocean] = useState<MetoceanData>(DEMO_METOCEAN);
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    // Dynamic update of Metocean Data based on active incident to simulate real telemetry sync
    setMetocean({
      ...DEMO_METOCEAN,
      lat: activeIncident.lat,
      lon: activeIncident.lon,
      windSpeed: activeIncident.id === 'INC-01' ? 4.2 : 5.1,
      currentSpeed: activeIncident.id === 'INC-01' ? 0.34 : 0.45
    });

    const fetchData = async () => {
      try {
        setLoading(true);
        // Use the actual demo spill ID expected by the backend
        const spillId = activeIncident.id; 
        
        const [
          spillData,
          driftData,
          apiVesselData
        ] = await Promise.all([
          api.getSpillSummary().catch(() => undefined),
          api.runDriftSimulation("test", 24, "backward").catch(() => undefined),
          api.getAISTracks().catch(() => [])
        ]);

        // Run these sequentially because both trigger heavy physics simulations
        const physicsData = await api.getPhysicsVerification("SLICK-IN-2026-009").catch(() => undefined);
        let rankData = await api.getFinalRanking("SLICK-IN-2026-009").catch(() => undefined);

        // --- MOCK OVERRIDES FOR SPECIFIC INCIDENTS ---
        let finalVessels: AISVesselTrack[] = [];
        let finalRanking: FinalRankingResponse | undefined = rankData;

        if (activeIncident.id === 'INC-01') {
          // Mumbai High Offshore Basin (Crude Oil)
          finalVessels = [
            { mmsi: 419001122, vessel_name: "MT DESH SHANTI", vessel_type: "Crude Tanker", flag: "India", imo: 9345678, closest_distance_km: 1.5, time_of_closest_approach: new Date().toISOString(), path: [{lat: 18.92, lon: 72.35, timestamp: new Date().toISOString(), speed_knots: 4.2, heading_deg: 120, course_deg: 120}] },
            { mmsi: 352001444, vessel_name: "PACIFIC ENERGY", vessel_type: "VLCC Tanker", flag: "Panama", imo: 9456789, closest_distance_km: 6.3, time_of_closest_approach: new Date().toISOString(), path: [{lat: 18.95, lon: 72.38, timestamp: new Date().toISOString(), speed_knots: 13.5, heading_deg: 180, course_deg: 180}] },
            { mmsi: 419009999, vessel_name: "Matsya Sagar 09", vessel_type: "Wooden Trawler", flag: "India", closest_distance_km: 2.0, time_of_closest_approach: new Date().toISOString(), path: [{lat: 18.91, lon: 72.33, timestamp: new Date().toISOString(), speed_knots: 3.2, heading_deg: 90, course_deg: 90}] },
          ];
          finalRanking = {
            spill_id: activeIncident.id,
            alpha_weight: 0.5,
            beta_weight: 0.5,
            rankings: [
              { rank: 1, mmsi: 419001122, vessel_name: "MT DESH SHANTI", vessel_type: "Crude Tanker", initial_score: 95, physics_score: 87, final_score: 91, rank_change: 0, evidence_for: ["Speed Anomaly: 14.8kn -> 4.2kn", "AIS Gap: 4h 15m"], evidence_against: [], ais_reliability: "LOW", investigation_priority: "HIGH", rank_change_explanation: "" },
              { rank: 2, mmsi: 352001444, vessel_name: "PACIFIC ENERGY", vessel_type: "VLCC Tanker", initial_score: 40, physics_score: 50, final_score: 45, rank_change: 0, evidence_for: ["Normal antenna switch"], evidence_against: [], ais_reliability: "HIGH", investigation_priority: "MEDIUM", rank_change_explanation: "" },
              { rank: 3, mmsi: 419009999, vessel_name: "Matsya Sagar 09", vessel_type: "Wooden Trawler", initial_score: 10, physics_score: 14, final_score: 12, rank_change: 0, evidence_for: ["Artisanal Craft (Exempt)"], evidence_against: [], ais_reliability: "HIGH", investigation_priority: "LOW", rank_change_explanation: "" },
            ]
          };
        } else if (activeIncident.id === 'INC-02') {
          // Chennai-Ennore Energy Corridor (Heavy Bunker Fuel)
          finalVessels = [
            { mmsi: 636015555, vessel_name: "MV OCEAN GLORY", vessel_type: "Bulk Carrier", flag: "Liberia", closest_distance_km: 2.6, time_of_closest_approach: new Date().toISOString(), path: [{lat: 13.23, lon: 80.33, timestamp: new Date().toISOString(), speed_knots: 12.1, heading_deg: 45, course_deg: 45}] },
            { mmsi: 419003344, vessel_name: "SS CHENNAI TRADER", vessel_type: "Container Ship", flag: "India", closest_distance_km: 8.9, time_of_closest_approach: new Date().toISOString(), path: [{lat: 13.25, lon: 80.35, timestamp: new Date().toISOString(), speed_knots: 18.2, heading_deg: 90, course_deg: 90}] },
          ];
          finalRanking = {
            spill_id: activeIncident.id,
            alpha_weight: 0.5,
            beta_weight: 0.5,
            rankings: [
              { rank: 1, mmsi: 636015555, vessel_name: "MV OCEAN GLORY", vessel_type: "Bulk Carrier", initial_score: 80, physics_score: 88, final_score: 84, rank_change: 0, evidence_for: ["AIS Gap: 3h 40m"], evidence_against: [], ais_reliability: "LOW", investigation_priority: "HIGH", rank_change_explanation: "" },
              { rank: 2, mmsi: 419003344, vessel_name: "SS CHENNAI TRADER", vessel_type: "Container Ship", initial_score: 20, physics_score: 24, final_score: 22, rank_change: 0, evidence_for: ["Steady transit"], evidence_against: [], ais_reliability: "HIGH", investigation_priority: "LOW", rank_change_explanation: "" },
            ]
          };
        } else {
          // Generic fallback
          finalVessels = apiVesselData || [];
        }

        if (spillData) setSpill(spillData);
        if (driftData) setDrift(driftData);
        setVessels(finalVessels);
        if (physicsData) setPhysics(physicsData);
        if (finalRanking) setRanking(finalRanking);
      } catch (err) {
        console.error('Error fetching API data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeIncident.id]);

  if (loading) {
    return (
      <div className="flex h-screen w-screen bg-[#070B12] text-[#F8FAFC] items-center justify-center font-mono">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-[#0284C7] border-t-transparent rounded-full animate-spin"></div>
          <p className="text-[#0284C7] tracking-widest text-sm">INITIALIZING SLICKTRACE FORENSIC ENGINE...</p>
          <p className="text-slate-500 text-xs">Connecting to {import.meta.env.VITE_API_URL || 'backend'}...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className={`flex flex-col h-screen w-screen overflow-hidden font-sans ${darkMode ? 'bg-[#070B12] text-[#F8FAFC]' : 'bg-[#F8FAFC] text-[#0F172A]'}`}>
          <TopBar 
            activeIncident={activeIncident} 
            setActiveIncident={setActiveIncident} 
            metocean={metocean} 
            darkMode={darkMode} 
            setDarkMode={setDarkMode} 
          />
          <HorizontalNav darkMode={darkMode} />
          <main className="flex-1 overflow-hidden relative">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage spill={spill} drift={drift} vessels={vessels} physics={physics} ranking={ranking} activeIncident={activeIncident} />} />
              <Route path="/sar-studio" element={<SatelliteStudioPage />} />
              <Route path="/drift-engine" element={<DriftBacktrackingPage drift={drift} activeIncident={activeIncident} />} />
              <Route path="/attribution" element={<VesselAttributionPage ranking={ranking} vessels={vessels} />} />
              <Route path="/evidence" element={<EvidenceCenterPage ranking={ranking} />} />
              <Route path="/analytics" element={<SpillAnalyticsPage ranking={ranking} physics={physics} />} />
              <Route path="/edge-lab" element={<SARDetectionLabPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
};
export default App;
