import React, { useState } from 'react';
import { FinalRankingResponse, AISVesselTrack, PhysicsVerificationResponse } from '../types';
import { Activity, Shield, FastForward, Settings2, ShieldCheck, Target, Crosshair } from 'lucide-react';

interface PanelCAttributionProps {
  ranking?: FinalRankingResponse;
  vessels: AISVesselTrack[];
  physics?: PhysicsVerificationResponse;
  selectedMmsi: number | null;
  setSelectedMmsi: (mmsi: number) => void;
}

export const PanelCAttribution: React.FC<PanelCAttributionProps> = ({ ranking, vessels, physics, selectedMmsi, setSelectedMmsi }) => {
  const [wDist, setWDist] = useState(0.4);
  const [wTime, setWTime] = useState(0.3);
  const [wGap, setWGap] = useState(0.3);

  const getPhysicsFit = (mmsi: number) => {
    if (!physics) return 'PENDING';
    const res = physics.results.find(r => r.mmsi === mmsi);
    return res?.classification || 'UNKNOWN';
  };

  return (
    <div className="h-full flex flex-col font-sans">
      <div className="p-2 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
        <h2 className="text-[10px] font-black text-slate-100 uppercase tracking-widest flex items-center gap-1.5">
          <Crosshair className="w-3.5 h-3.5 text-rose-400" />
          Vessel Attribution & Counterfactual Verifier
        </h2>
        <span className="text-[8px] font-mono text-rose-400 bg-rose-500/10 px-1 py-0.5 rounded border border-rose-500/20 flex items-center gap-1">
          <Activity className="w-2.5 h-2.5" /> ISOLATION FOREST
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3 custom-scrollbar">
        
        {/* Sliders & Toggles */}
        <div className="bg-slate-950 border border-slate-800 rounded p-2 flex gap-3">
          <div className="flex-[2]">
            <h3 className="text-[8px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1 mb-1.5 border-b border-slate-800 pb-1">
              <Settings2 className="w-2.5 h-2.5" /> Explainable Attribution (w)
            </h3>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[8px] font-mono text-slate-400">
                <span className="w-10">W_DIST</span>
                <input type="range" min={0} max={1} step={0.1} value={wDist} onChange={e=>setWDist(+e.target.value)} className="flex-1 h-0.5 accent-cyan-500" />
                <span className="w-6 text-right text-cyan-400">{wDist}</span>
              </div>
              <div className="flex items-center gap-2 text-[8px] font-mono text-slate-400">
                <span className="w-10">W_TIME</span>
                <input type="range" min={0} max={1} step={0.1} value={wTime} onChange={e=>setWTime(+e.target.value)} className="flex-1 h-0.5 accent-cyan-500" />
                <span className="w-6 text-right text-cyan-400">{wTime}</span>
              </div>
              <div className="flex items-center gap-2 text-[8px] font-mono text-slate-400">
                <span className="w-10">W_GAP</span>
                <input type="range" min={0} max={1} step={0.1} value={wGap} onChange={e=>setWGap(+e.target.value)} className="flex-1 h-0.5 accent-rose-500" />
                <span className="w-6 text-right text-rose-400">{wGap}</span>
              </div>
            </div>
          </div>
          <div className="flex-1 border-l border-slate-800 pl-3 flex flex-col gap-1.5">
            <h3 className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">Automated Guards</h3>
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded p-1 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span className="text-[8px] font-bold text-emerald-500 uppercase">Artisanal Craft Shield</span>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 rounded p-1 flex items-center gap-1">
              <Shield className="w-3 h-3 text-amber-400" />
              <span className="text-[8px] font-bold text-amber-500 uppercase">Speed Drop Tracker</span>
            </div>
          </div>
        </div>

        {/* Counterfactual Execute */}
        <button className="w-full bg-rose-600/20 hover:bg-rose-600/40 border border-rose-500/50 text-rose-300 rounded py-2 text-[10px] font-black uppercase tracking-widest flex justify-center items-center gap-2 transition-all shadow-[0_0_10px_rgba(225,29,72,0.2)] hover:shadow-[0_0_15px_rgba(225,29,72,0.4)]">
          <FastForward className="w-3.5 h-3.5" /> Execute Counterfactual Sweep
        </button>

        {/* Candidate List */}
        <div className="flex-1 bg-slate-950 border border-slate-800 rounded flex flex-col">
          <div className="grid grid-cols-5 text-[8px] font-bold uppercase tracking-wider text-slate-500 bg-slate-900/50 p-2 border-b border-slate-800">
            <div className="col-span-2">Candidate Vessel</div>
            <div className="text-center">AIS Gap</div>
            <div className="text-center">Physics Fit</div>
            <div className="text-right">Score</div>
          </div>
          <div className="overflow-y-auto flex-1 p-1 space-y-1">
            {ranking?.rankings.slice(0, 4).map((candidate, idx) => {
              const isSelected = selectedMmsi === candidate.mmsi;
              const fit = getPhysicsFit(candidate.mmsi);
              const fitColor = fit.includes('HIGH') ? 'text-rose-400' : fit.includes('MEDIUM') ? 'text-amber-400' : 'text-emerald-400';
              
              return (
                <div 
                  key={candidate.mmsi}
                  onClick={() => setSelectedMmsi(candidate.mmsi)}
                  className={`grid grid-cols-5 items-center p-2 rounded cursor-pointer border transition-all ${
                    isSelected ? 'bg-cyan-950/40 border-cyan-500/50' : 'bg-transparent border-transparent hover:bg-slate-900'
                  }`}
                >
                  <div className="col-span-2 flex flex-col">
                    <span className={`text-[10px] font-bold truncate ${isSelected ? 'text-cyan-400' : 'text-slate-200'}`}>
                      {candidate.vessel_name}
                    </span>
                    <span className="text-[8px] font-mono text-slate-500">{candidate.mmsi}</span>
                  </div>
                  <div className="text-center text-[9px] font-mono text-amber-400">
                    {candidate.ais_reliability === 'LOW' ? 'DETECTED' : 'CLEAR'}
                  </div>
                  <div className={`text-center text-[9px] font-bold ${fitColor}`}>
                    {fit}
                  </div>
                  <div className="text-right text-[10px] font-mono font-bold text-slate-200">
                    {candidate.final_score.toFixed(1)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
};
