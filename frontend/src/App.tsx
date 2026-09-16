import React, { useState, useEffect, Component, ErrorInfo, ReactNode } from 'react';
import { api } from './services/api';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { PageType, Incident, MetoceanData, DEMO_INCIDENTS, DEMO_METOCEAN } from './types/app';
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
        <div className="flex h-screen w-screen bg-[#060b14] text-slate-100 items-center justify-center font-mono p-8">
          <div className="max-w-xl w-full border border-rose-500/40 rounded-lg p-6 bg-rose-950/20 space-y-4">
            <h1 className="text-rose-400 text-lg font-bold tracking-widest">⚠ SYSTEM ERROR</h1>
            <p className="text-slate-300 text-sm">{this.state.error.message}</p>
            <pre className="text-xs text-slate-500 overflow-auto max-h-48">{this.state.error.stack}</pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-sm"
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
  const [activePage, setActivePage] = useState<PageType>('dashboard');
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
      <div className="flex h-screen w-screen bg-[#060b14] text-slate-100 items-center justify-center font-mono">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-cyan-400 tracking-widest text-sm">INITIALIZING SLICKTRACE FORENSIC ENGINE...</p>
          <p className="text-slate-500 text-xs">Connecting to {import.meta.env.VITE_API_URL || 'backend'}...</p>
        </div>
      </div>
    );
  }

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardPage spill={spill} drift={drift} vessels={vessels} physics={physics} ranking={ranking} activeIncident={activeIncident} />;
      case 'drift-backtracking':
        return <DriftBacktrackingPage drift={drift} activeIncident={activeIncident} onNavigate={setActivePage} />;
      case 'vessel-attribution':
        return <VesselAttributionPage ranking={ranking} vessels={vessels} />;
      case 'evidence-center':
        return <EvidenceCenterPage ranking={ranking} />;
      case 'satellite-studio':
        return <SatelliteStudioPage />;
      case 'spill-analytics':
        return <SpillAnalyticsPage ranking={ranking} physics={physics} />;
      case 'sar-detection-lab':
        return <SARDetectionLabPage />;
      default:
        return <DashboardPage spill={spill} drift={drift} vessels={vessels} physics={physics} ranking={ranking} activeIncident={activeIncident} />;
    }
  };

  return (
    <ErrorBoundary>
      <div className={`flex h-screen w-screen overflow-hidden font-sans ${darkMode ? 'bg-[#060b14] text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
        <Sidebar activePage={activePage} setActivePage={setActivePage} />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar 
            activeIncident={activeIncident} 
            setActiveIncident={setActiveIncident} 
            metocean={metocean} 
            darkMode={darkMode} 
            setDarkMode={setDarkMode} 
          />
          <main className="flex-1 overflow-hidden relative">
            {renderPage()}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
};
export default App;
