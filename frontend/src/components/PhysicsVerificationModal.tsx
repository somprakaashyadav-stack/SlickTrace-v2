import React from 'react';
import { ShieldCheck, Target, Layers, MapPin, Clock, Wind, Activity, X } from 'lucide-react';
import { PhysicsVerificationResult, FinalCandidateRanking } from '../types';

interface PhysicsVerificationModalProps {
  result: PhysicsVerificationResult;
  candidate: FinalCandidateRanking;
  onClose: () => void;
  isDemoMode?: boolean;
}

export const PhysicsVerificationModal: React.FC<PhysicsVerificationModalProps> = ({ 
  result, 
  candidate, 
  onClose,
  isDemoMode = true 
}) => {
  const metrics = result.metrics;
  const scenario = result.best_scenario;

  return (
    <div className="fixed inset-0 z-[9999] bg-navy-950/80 backdrop-blur-md flex items-center justify-center p-6">
      <div className="bg-navy-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-6xl max-h-full flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-navy-950">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg text-purple-400">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-100 uppercase tracking-widest">Physics Verification Report</h2>
              <p className="text-xs text-slate-400 font-mono flex items-center gap-3">
                <span>Vessel: {candidate.vessel_name} (MMSI: {candidate.mmsi})</span>
                {isDemoMode && (
                  <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded font-bold">
                    DEMO PHYSICS ENGINE ACTIVE
                  </span>
                )}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Top Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-navy-950 border border-slate-800">
              <div className="text-slate-500 mb-1 font-mono text-[10px] flex items-center gap-2 uppercase">
                <MapPin className="w-3.5 h-3.5 text-cyan-400" /> Assumed Release
              </div>
              <div className="font-bold text-slate-200">
                {scenario.release_lat.toFixed(4)}°N, {scenario.release_lon.toFixed(4)}°E
              </div>
            </div>
            <div className="p-4 rounded-xl bg-navy-950 border border-slate-800">
              <div className="text-slate-500 mb-1 font-mono text-[10px] flex items-center gap-2 uppercase">
                <Clock className="w-3.5 h-3.5 text-cyan-400" /> Est Release Time
              </div>
              <div className="font-bold text-slate-200">
                T-minus {scenario.duration_hours} hours
              </div>
            </div>
            <div className="p-4 rounded-xl bg-navy-950 border border-slate-800">
              <div className="text-slate-500 mb-1 font-mono text-[10px] flex items-center gap-2 uppercase">
                <Wind className="w-3.5 h-3.5 text-cyan-400" /> Scenario Params
              </div>
              <div className="text-sm font-bold text-slate-200">
                Wind Var: {scenario.wind_variance}%
              </div>
            </div>
            <div className="p-4 rounded-xl bg-purple-900/20 border border-purple-500/30">
              <div className="text-purple-400/70 mb-1 font-mono text-[10px] flex items-center gap-2 uppercase font-bold">
                <ShieldCheck className="w-3.5 h-3.5" /> Physics Score
              </div>
              <div className="text-2xl font-black text-purple-400">
                {result.physics_consistency_score}/100
              </div>
            </div>
          </div>

          {/* Visualization Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Visual Output */}
            <div className="rounded-xl border border-slate-800 overflow-hidden bg-navy-950 flex flex-col">
              <div className="p-3 border-b border-slate-800 bg-slate-900/50">
                <h3 className="text-sm font-bold text-slate-300 font-mono tracking-wider text-center">
                  OBSERVED SLICK vs SIMULATED SLICK
                </h3>
              </div>
              <div className="flex-1 min-h-[350px] relative p-4 flex items-center justify-center bg-[#0a192f]">
                {/* Abstract visualization of the overlap */}
                <div className="relative w-full max-w-[300px] aspect-square">
                  {/* Grid background */}
                  <div className="absolute inset-0 border border-slate-800 opacity-20 rounded-full" style={{ backgroundImage: 'radial-gradient(#1e293b 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
                  
                  {/* Observed Polygon */}
                  <div className="absolute inset-4 border-2 border-sky-400/50 bg-sky-400/20 rounded-[40%_60%_70%_30%_/_40%_50%_60%_50%] animate-[spin_20s_linear_infinite]" style={{ animationDirection: 'reverse' }}></div>
                  
                  {/* Simulated Particle Cloud (position depends on spatial overlap) */}
                  <div className="absolute inset-8 border border-purple-500/50 bg-purple-500/30 rounded-[60%_40%_30%_70%_/_50%_60%_40%_50%] animate-[spin_15s_linear_infinite]" 
                       style={{ 
                         transform: `translate(${Math.max(0, 100 - metrics.spatial_overlap_pct) / 2}px, ${Math.max(0, 100 - metrics.spatial_overlap_pct) / 2}px)`
                       }}>
                  </div>

                  {/* Centroids */}
                  <div className="absolute top-1/2 left-1/2 w-3 h-3 bg-sky-400 rounded-full -translate-x-1/2 -translate-y-1/2 shadow-[0_0_10px_rgba(56,189,248,0.8)]"></div>
                  <div className="absolute top-1/2 left-1/2 w-3 h-3 bg-purple-500 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.8)]"
                       style={{ transform: `translate(calc(-50% + ${Math.max(0, 100 - metrics.spatial_overlap_pct)}px), calc(-50% + ${Math.max(0, 100 - metrics.spatial_overlap_pct)}px))` }}>
                  </div>
                  
                  {/* Trajectory line */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-50">
                    <path d="M 20 280 Q 150 150 150 150" fill="transparent" stroke="#a855f7" strokeWidth="2" strokeDasharray="5,5" />
                  </svg>
                </div>
                
                <div className="absolute bottom-4 left-4 right-4 flex justify-between text-[10px] font-mono">
                  <div className="flex items-center gap-2"><div className="w-3 h-3 bg-sky-400/50 border border-sky-400"></div> Observed</div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 bg-purple-500/50 border border-purple-500"></div> Simulated</div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-white"></div> Centroid</div>
                </div>
              </div>
            </div>

            {/* Metrics Panel */}
            <div className="space-y-4 flex flex-col">
              <div className="p-5 rounded-xl bg-navy-950 border border-slate-800 flex-1">
                <h3 className="text-sm font-bold text-slate-300 font-mono tracking-wider mb-6 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400" /> Convergence Metrics
                </h3>
                
                <div className="space-y-5">
                  <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-slate-400">Spatial Overlap</span>
                      <span className="text-slate-200 font-bold">{metrics.spatial_overlap_pct.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${metrics.spatial_overlap_pct}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-slate-400">Centroid Error</span>
                      <span className="text-slate-200 font-bold">{metrics.centroid_error_km.toFixed(2)} km</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${Math.max(0, 100 - (metrics.centroid_error_km * 5))}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-slate-400">Shape Similarity</span>
                      <span className="text-slate-200 font-bold">{metrics.shape_similarity_score.toFixed(1)}/100</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${metrics.shape_similarity_score}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-slate-400">Orientation Similarity</span>
                      <span className="text-slate-200 font-bold">{metrics.orientation_similarity_score.toFixed(1)}/100</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${metrics.orientation_similarity_score}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-slate-400">Timing Consistency Error</span>
                      <span className="text-slate-200 font-bold">{metrics.timing_error_hours.toFixed(1)} hrs</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${Math.max(0, 100 - (metrics.timing_error_hours * 10))}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Rationale Panel */}
              <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700">
                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Rank Shift Rationale</h4>
                <p className="text-sm text-slate-200 leading-relaxed italic">
                  "{candidate.rank_change_explanation}"
                </p>
                <div className="mt-3 text-xs text-slate-500 font-mono">
                  Initial AIS Rank: #{candidate.rank - candidate.rank_change} → Final Integrated Rank: #{candidate.rank}
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};
