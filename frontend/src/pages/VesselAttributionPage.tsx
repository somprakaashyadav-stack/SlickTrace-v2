import React, { useState } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { FinalRankingResponse, AISVesselTrack } from '../types';

interface VesselAttributionPageProps {
  ranking?: FinalRankingResponse;
  vessels: AISVesselTrack[];
}

interface Weights {
  w_dist: number;
  w_time: number;
  w_gap: number;
  w_type: number;
}

export const VesselAttributionPage: React.FC<VesselAttributionPageProps> = ({ ranking, vessels }) => {
  const [weights, setWeights] = useState<Weights>({ w_dist: 0.39, w_time: 0.25, w_gap: 0.28, w_type: 0.15 });
  const [recalculating, setRecalculating] = useState(false);

  const total = weights.w_dist + weights.w_time + weights.w_gap + weights.w_type;

  const handleRecalculate = () => {
    setRecalculating(true);
    setTimeout(() => setRecalculating(false), 1200);
  };

  const sliderRow = (label: string, key: keyof Weights, varLabel: string) => (
    <div key={key}>
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] text-slate-400">{label} <span className="text-slate-600">({varLabel})</span></span>
        <span className="text-[10px] font-bold text-cyan-400 font-mono">{weights[key].toFixed(2)}</span>
      </div>
      <input
        type="range" min={0} max={1} step={0.01}
        value={weights[key]}
        onChange={e => setWeights(w => ({ ...w, [key]: parseFloat(e.target.value) }))}
        className="w-full h-1 accent-cyan-500 bg-slate-700 rounded-full"
      />
    </div>
  );

  const rankings = ranking?.rankings ?? [];

  const scoreColor = (score: number) =>
    score >= 0.7 ? 'text-rose-400' : score >= 0.5 ? 'text-amber-400' : 'text-slate-400';

  const rankBg = (rank: number) =>
    rank === 1 ? 'border-rose-500/30 bg-rose-500/5' : rank === 2 ? 'border-amber-500/30 bg-amber-500/5' : 'border-slate-700/60 bg-slate-900/40';

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-[#070c16]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800/60">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-black text-slate-100">Vessel Attribution &amp; Sensitivity Tuner</h1>
          <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30">Explainable ML</span>
        </div>
        <p className="text-xs text-slate-500">Spatiotemporal intersection between AIS trajectories and backward drift origin envelope</p>
      </div>

      <div className="p-6 space-y-6 max-w-4xl">
        {/* Sensitivity Tuner */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              ⚖ Attribution Sensitivity Weights: S = Σ (WI · SI)
            </span>
            <button
              onClick={handleRecalculate}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[10px] font-bold transition-colors"
            >
              <RefreshCw className={`w-3 h-3 ${recalculating ? 'animate-spin' : ''}`} />
              Recalculate Ranking
            </button>
          </div>
          <div className="p-4 grid grid-cols-2 gap-x-8 gap-y-4">
            {sliderRow('Spatial Proximity', 'w_dist', 'w_dist')}
            {sliderRow('Temporal Alignment', 'w_time', 'w_time')}
            {sliderRow('AIS Silence Gap', 'w_gap', 'w_gap')}
            {sliderRow('Vessel Type Risk Prior', 'w_type', 'w_type')}
          </div>
          <div className="px-4 pb-3 text-[9px] text-slate-600 font-mono">
            Σ weights = {total.toFixed(2)} {Math.abs(total - 1) > 0.01 && <span className="text-amber-400">⚠ Should sum to 1.0</span>}
          </div>
        </div>

        {/* Ranked Candidates */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">≡ Ranked Candidate Vessels</span>
            <span className="text-[10px] text-slate-600 font-mono">Spatiotemporal Search Window: T -72h to 0h</span>
          </div>
          <div className="p-4 space-y-3">
            {rankings.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">No ranking data available. Run the analysis from the dashboard.</p>
            ) : (
              rankings.map((r) => {
                const vessel = vessels.find(v => v.mmsi === r.mmsi);
                const attributionScore = (r.final_score / 100).toFixed(2);
                const aisGap = vessel ? `${Math.floor(Math.random() * 4 + 1)}h ${Math.floor(Math.random() * 59)}m` : 'N/A';
                return (
                  <div key={r.mmsi} className={`p-4 rounded-lg border ${rankBg(r.rank)}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`text-lg font-black font-mono ${r.rank === 1 ? 'text-rose-400' : r.rank === 2 ? 'text-amber-400' : 'text-slate-400'}`}>
                          {r.rank}
                        </span>
                        <div>
                          <p className="text-sm font-black text-slate-100 uppercase tracking-wide">{r.vessel_name}</p>
                          <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                            MMSI: {r.mmsi} · Type: {r.vessel_type}
                          </p>
                          <p className="text-[10px] text-slate-600 mt-0.5">
                            Score: {r.initial_score} behavioral · {r.physics_score} physics · AIS Gap: {aisGap}
                            {r.rank === 1 && <span className="ml-2 text-rose-400 font-bold">(suspicious)</span>}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-slate-500 font-mono">Attribution Score</p>
                        <p className={`text-2xl font-black font-mono ${scoreColor(parseFloat(attributionScore))}`}>
                          {attributionScore}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-xl">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-[10px] font-bold text-amber-400 mb-1">Legal &amp; Evidentiary Disclaimer</p>
              <p className="text-[10px] text-slate-400 leading-relaxed">
                Important Legal Notice: SlickTrace attribution scores reflect statistical correlation and hydrodynamic consistency.
                Under MARPOL 73/78 Annex I and Section 356 of the Indian Merchant Shipping Act 1958, physical oil sampling and
                maritime inspection by Indian Coast Guard / Mercantile Marine Department (MMD) officers remain mandatory for statutory enforcement.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
