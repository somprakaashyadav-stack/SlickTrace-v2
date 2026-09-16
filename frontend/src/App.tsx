import React, { useState, useEffect } from 'react';
import { InvestigatorDashboard } from './components/InvestigatorDashboard';
import { api } from './services/api';
import {
  SpillSummary,
  DriftSimulation,
  AISVesselTrack,
  PhysicsVerificationResponse,
  FinalRankingResponse
} from './types';

export const App: React.FC = () => {
  const [spill, setSpill] = useState<SpillSummary>();
  const [drift, setDrift] = useState<DriftSimulation>();
  const [vessels, setVessels] = useState<AISVesselTrack[]>([]);
  const [physics, setPhysics] = useState<PhysicsVerificationResponse>();
  const [ranking, setRanking] = useState<FinalRankingResponse>();
  const [loading, setLoading] = useState<boolean>(true);

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
        // Running them in parallel overloads the backend and causes timeouts
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
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen w-screen bg-navy-950 text-slate-100 items-center justify-center font-mono">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-cyan-400 tracking-widest text-sm">INITIALIZING SLICKTRACE FORENSIC ENGINE...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-navy-950 text-slate-100 overflow-hidden font-sans">
      <InvestigatorDashboard 
        spill={spill}
        drift={drift}
        vessels={vessels}
        physics={physics}
        ranking={ranking}
      />
    </div>
  );
};
export default App;
