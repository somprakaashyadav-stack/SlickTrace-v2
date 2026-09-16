import React, { useState, useEffect, Component, ErrorInfo, ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { api } from './services/api';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { Incident, MetoceanData, DEMO_INCIDENTS, DEMO_METOCEAN } from './types/app';
import {
  SpillSummary,
  DriftSimulation,
  AISVesselTrack,
  PhysicsVerificationResponse,
  FinalRankingResponse
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
    const fetchData = async () => {
      try {
        setLoading(true);
        // Use the actual demo spill ID expected by the backend
        const spillId = "SLICK-IN-2026-009"; 
        
        const [
          spillData,
          driftData,
          vesselData
        ] = await Promise.all([
          api.getSpillSummary().catch(() => undefined),
          api.runDriftSimulation("test", 24, "backward").catch(() => undefined),
          api.getAISTracks().catch(() => [])
        ]);

        // Run these sequentially because both trigger heavy physics simulations
        const physicsData = await api.getPhysicsVerification(spillId).catch(() => undefined);
        const rankData = await api.getFinalRanking(spillId).catch(() => undefined);

        if (spillData) setSpill(spillData);
        if (driftData) setDrift(driftData);
        if (vesselData) setVessels(vesselData);
        if (physicsData) setPhysics(physicsData);
        if (rankData) setRanking(rankData);
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
        <div className={`flex h-screen w-screen overflow-hidden font-sans ${darkMode ? 'bg-[#070B12] text-[#F8FAFC]' : 'bg-[#F8FAFC] text-[#0F172A]'}`}>
          <Sidebar darkMode={darkMode} />
          <div className="flex-1 flex flex-col min-w-0">
            <TopBar 
              activeIncident={activeIncident} 
              setActiveIncident={setActiveIncident} 
              metocean={metocean} 
              darkMode={darkMode} 
              setDarkMode={setDarkMode} 
            />
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
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
};
export default App;
