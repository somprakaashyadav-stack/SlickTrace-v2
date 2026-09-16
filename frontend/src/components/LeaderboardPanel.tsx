import React from 'react';
import { FinalRankingResponse, AISVesselTrack, SpillSummary, DriftSimulation, PhysicsVerificationResponse } from '../types';
import { AlertTriangle, Clock, Search, Filter, Activity, Trophy, ArrowDown, ChevronRight, Navigation } from 'lucide-react';

interface LeaderboardPanelProps {
  ranking?: FinalRankingResponse;
  vessels: AISVesselTrack[];
  spill?: SpillSummary;
  drift?: DriftSimulation;
  physics?: PhysicsVerificationResponse;
  selectedMmsi: number | null;
  setSelectedMmsi: (mmsi: number) => void;
}

export const LeaderboardPanel: React.FC<LeaderboardPanelProps> = ({ ranking, vessels, spill, drift, physics, selectedMmsi, setSelectedMmsi }) => {
  if (!ranking || ranking.rankings.length === 0) {
    return (
      <div className="w-[380px] bg-navy-950 border-r border-slate-800 flex flex-col items-center justify-center p-6 text-center shrink-0">
        <p className="text-xs text-slate-500 font-mono">Loading Investigation Pipeline...</p>
      </div>
    );
  }

  const getVesselFlag = (mmsi: number) => {
    const vessel = vessels.find(v => v.mmsi === mmsi);
    return vessel?.flag || 'UNKN';
  };

  const getPhysicsFit = (mmsi: number) => {
    if (!physics) return 'PENDING';
    const res = physics.results.find(r => r.mmsi === mmsi);
    return res?.classification || 'UNKNOWN';
  };

  const PipelineStep = ({ icon: Icon, title, active, children, line = true }: any) => (
    <div className="flex gap-4 relative">
      {line && <div className="absolute top-8 bottom-[-16px] left-3.5 w-0.5 bg-slate-800" />}
      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border-2 z-10 ${active ? 'bg-cyan-950 border-cyan-500 text-cyan-400' : 'bg-slate-900 border-slate-700 text-slate-500'}`}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1 pb-6">
        <h3 className={`text-[10px] font-bold uppercase tracking-widest mb-2 ${active ? 'text-slate-200' : 'text-slate-500'}`}>{title}</h3>
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-3">
          {children}
        </div>
      </div>
    </div>
  );

  return (
    <div className="w-[380px] bg-[#050a12] border-r border-slate-800 flex flex-col shrink-0 overflow-hidden font-sans">
      <div className="p-4 border-b border-slate-800 bg-slate-900/40">
        <h2 className="text-xs font-black text-slate-100 uppercase tracking-widest flex items-center gap-2">
          <Navigation className="w-4 h-4 text-cyan-400" />
          Forensic Pipeline
        </h2>
        <p className="text-[10px] text-slate-400 mt-1">Algorithmic Correlation Workflow</p>
      </div>

      <div className="flex-1 overflow-y-auto p-5 pb-10 custom-scrollbar">
        
        {/* Step 1: Detection */}
        <PipelineStep icon={AlertTriangle} title="Oil Spill Detected" active={true}>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Confidence</span>
            <span className="font-mono text-emerald-400 font-bold">{spill?.confidence_score}%</span>
          </div>
          <div className="flex justify-between items-center text-xs mt-1">
            <span className="text-slate-400">Area</span>
            <span className="font-mono text-cyan-400 font-bold">{spill?.area_sq_km} km²</span>
          </div>
        </PipelineStep>

        {/* Step 2: Hindcast */}
        <PipelineStep icon={Clock} title="Backward Hindcast" active={true}>
          <div className="flex justify-between items-center text-xs mb-1">
            <span className="text-slate-400">Probable Origin</span>
            <span className="font-mono text-amber-400 font-bold">
              {drift?.origin_candidate ? 'ISOLATED' : 'CALCULATING'}
            </span>
          </div>
          <div className="flex justify-between items-center text-[10px]">
            <span className="text-slate-500">Time Window</span>
            <span className="font-mono text-slate-300">T0 ± {drift?.origin_candidate ? Math.round(drift.origin_candidate.delta_t_hours) : '--'}h</span>
          </div>
          <div className="flex justify-between items-center text-[10px] mt-0.5">
            <span className="text-slate-500">Uncertainty Radius</span>
            <span className="font-mono text-slate-300">{drift?.origin_candidate?.uncertainty_radius_km.toFixed(1) || '--'} km</span>
          </div>
        </PipelineStep>

        {/* Step 3: AIS Search & Filter */}
        <PipelineStep icon={Search} title="AIS Search & Filter" active={true}>
          <div className="flex items-center justify-between">
            <div className="text-center">
              <p className="text-lg font-black text-slate-200 font-mono">{vessels.length}</p>
              <p className="text-[9px] text-slate-500 uppercase">Vessels Found</p>
            </div>
            <Filter className="w-4 h-4 text-slate-600" />
            <div className="text-center">
              <p className="text-lg font-black text-cyan-400 font-mono">{ranking.rankings.length}</p>
              <p className="text-[9px] text-cyan-600 uppercase">Candidates</p>
            </div>
          </div>
        </PipelineStep>

        {/* Step 4: Physics & Final Ranking */}
        <PipelineStep icon={Activity} title="Counterfactual Physics & Final Ranking" active={true} line={false}>
          <div className="space-y-2 mt-1">
            {ranking.rankings.slice(0, 3).map((candidate, idx) => {
              const isSelected = selectedMmsi === candidate.mmsi;
              const fit = getPhysicsFit(candidate.mmsi);
              const fitColor = fit.includes('HIGH') ? 'text-rose-400' : fit.includes('MEDIUM') ? 'text-amber-400' : 'text-emerald-400';
              const fitBg = fit.includes('HIGH') ? 'bg-rose-500/10 border-rose-500/30' : fit.includes('MEDIUM') ? 'bg-amber-500/10 border-amber-500/30' : 'bg-emerald-500/10 border-emerald-500/30';
              
              const medals = ['🥇', '🥈', '🥉'];
              
              return (
                <div 
                  key={candidate.mmsi}
                  onClick={() => setSelectedMmsi(candidate.mmsi)}
                  className={`relative p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected ? 'bg-cyan-950/40 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.15)]' : 'bg-[#0a111a] border-slate-700/50 hover:border-slate-500'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{medals[idx]}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-bold truncate uppercase ${isSelected ? 'text-cyan-400' : 'text-slate-200'}`}>
                        {candidate.vessel_name}
                      </p>
                      <p className="text-[9px] text-slate-500 font-mono">MMSI: {candidate.mmsi}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-[10px] mt-2 pt-2 border-t border-slate-800/60">
                    <div className="flex flex-col">
                      <span className="text-slate-500">Physics Fit</span>
                      <span className={`font-bold ${fitColor}`}>{fit}</span>
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="text-slate-500">Final Score</span>
                      <span className="font-bold text-slate-200 font-mono">{candidate.final_score} / 100</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
          <div className="mt-4 flex flex-col items-center justify-center p-3 bg-amber-500/5 border border-amber-500/20 rounded border-dashed">
             <Trophy className="w-4 h-4 text-amber-500 mb-1" />
             <p className="text-[10px] text-amber-400 font-bold uppercase text-center">Investigator Decision Required</p>
             <p className="text-[9px] text-amber-500/70 text-center mt-1">Select a candidate above to review evidence and generate final dossier.</p>
          </div>
        </PipelineStep>
      </div>
    </div>
  );
};
