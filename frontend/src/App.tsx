import React, { useState, useEffect, Component, ErrorInfo, ReactNode } from 'react';
import { api } from './services/api';
import { C4ISRDashboard } from './components/C4ISRDashboard';
import { Incident, MetoceanData, DEMO_INCIDENTS, DEMO_METOCEAN } from './types/app';
import {
  SpillSummary,
  DriftSimulation,
  AISVesselTrack,
  PhysicsVerificationResponse,
  FinalRankingResponse
} from './types';

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
  const [activeIncident, setActiveIncident] = useState<Incident>(DEMO_INCIDENTS[0]);
  const [metocean] = useState<MetoceanData>(DEMO_METOCEAN);

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
      <div className="flex h-screen w-screen bg-[#050a12] text-slate-100 items-center justify-center font-mono">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-cyan-400 tracking-widest text-sm">INITIALIZING SLICKTRACE C4ISR MARITIME RECONNAISSANCE...</p>
          <p className="text-slate-500 text-xs">Connecting to {import.meta.env.VITE_API_URL || 'backend'}...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <C4ISRDashboard 
        spill={spill} 
        drift={drift} 
        vessels={vessels} 
        physics={physics} 
        ranking={ranking}
        activeIncident={activeIncident}
        setActiveIncident={setActiveIncident}
        metocean={metocean}
      />
    </ErrorBoundary>
  );
};
export default App;
