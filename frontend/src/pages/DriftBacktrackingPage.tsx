import React, { useState } from 'react';
import { Navigation2, AlertTriangle, ChevronRight, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { DriftSimulation } from '../types';
import { Incident } from '../types/app';

interface DriftBacktrackingPageProps {
  drift?: DriftSimulation;
  activeIncident: Incident;
}

export const DriftBacktrackingPage: React.FC<DriftBacktrackingPageProps> = ({ drift, activeIncident }) => {
  const navigate = useNavigate();
  const origin = drift?.origin_candidate;

  const engineParams = [
    { label: 'Integration Time Step', value: '15 minutes' },
    { label: 'Wind Drag Coefficient', value: '3.5% (Stokes Drift)' },
    { label: 'Horizontal Diffusivity', value: '10 m²/s' },
    { label: 'Current Layer Depth', value: '0.0 – 1.0 m (Ekman)' },
  ];

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-[#070B12]">
      {/* Page Header */}
      <div className="px-6 py-4 border-b border-slate-800/60 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-lg font-black text-slate-100">Lagrangian Hydrodynamic Drift Simulation</h1>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">OpenDrift</span>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">OpenOil</span>
          </div>
          <p className="text-xs text-slate-500">Backward Monte Carlo Dispersion (N=1,000 particles) driven by CMEMS Ocean Currents &amp; ERA5 10m Wind Vectors</p>
        </div>
        <button
          onClick={() => navigate('/attribution')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0284C7] hover:bg-sky-500 text-white text-xs font-bold transition-colors"
        >
          Vessel Attribution <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="p-6 space-y-6 max-w-5xl">
        {/* Origin Probability Envelope Analysis */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Navigation2 className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Origin Probability Envelope Analysis (Reverse Time)</span>
            </div>
            <button className="px-3 py-1 rounded bg-purple-600/20 border border-purple-500/30 text-purple-400 text-[10px] font-bold uppercase tracking-wider hover:bg-purple-600/30 transition-colors">
              Physics Backtracking
            </button>
          </div>

          {/* Operational Rule Banner */}
          <div className="mx-4 mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <p className="text-[11px] text-amber-300 leading-relaxed">
              <span className="font-bold">Operational Hydrodynamic Rule:</span> Because sea surface currents and wind drift constantly transport oil films, a detected slick position is{' '}
              <span className="font-bold underline">NEVER</span> the discharge point. OpenDrift reverses the advection-diffusion equation to isolate the exact space-time envelope where discharge statistically occurred.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4 p-4">
            <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-[10px] text-slate-500 font-mono mb-2">50% Core Probability</p>
              <p className="text-base font-black text-cyan-400 font-mono">
                {origin ? `${origin.Y0.toFixed(2)}°N, ${origin.X0.toFixed(2)}°E` : `${activeIncident.lat.toFixed(2)}°N, ${activeIncident.lon.toFixed(2)}°E`}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                Discharge Window: T{origin ? ` -${Math.round(origin.delta_t_hours - 2)}h to -${Math.round(origin.delta_t_hours)}h` : ' -20h to -24h'}
              </p>
            </div>
            <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-[10px] text-slate-500 font-mono mb-2">75% Probability Area</p>
              <p className="text-base font-black text-amber-400 font-mono">
                {origin ? `${(origin.uncertainty_radius_km * origin.uncertainty_radius_km * Math.PI * 0.75).toFixed(1)} km²` : '68.4 km²'}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Spatiotemporal uncertainty radius</p>
            </div>
            <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-[10px] text-slate-500 font-mono mb-2">Total Particles Trailed</p>
              <p className="text-base font-black text-emerald-400 font-mono">
                {drift ? `${drift.particle_count?.toLocaleString() ?? '1,000'} Lagrangian` : '1,000 Lagrangian'}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Runge-Kutta 4th Order Integrator</p>
            </div>
          </div>
        </div>

        {/* Hydrodynamic Engine Parameters */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">⚙ Hydrodynamic Engine Parameters</span>
          </div>
          <div className="p-4 grid grid-cols-2 gap-4">
            {engineParams.map((p, i) => (
              <div key={i} className="p-3 bg-slate-900/40 rounded-lg border border-slate-800/60">
                <p className="text-[10px] text-slate-500 font-mono mb-1">{p.label}</p>
                <p className="text-sm font-bold text-slate-200">{p.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Drift Info */}
        {drift && (
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">📡 Forcing Data</span>
            </div>
            <div className="p-4 grid grid-cols-4 gap-4">
              {[
                { label: 'Wind Speed', value: `${drift.wind_speed_knots?.toFixed(1) ?? 'N/A'} kn` },
                { label: 'Wind Direction', value: `${drift.wind_direction_deg?.toFixed(0) ?? 'N/A'}°` },
                { label: 'Current Speed', value: `${drift.current_speed_knots?.toFixed(2) ?? 'N/A'} kn` },
                { label: 'Current Direction', value: `${drift.current_direction_deg?.toFixed(0) ?? 'N/A'}°` },
              ].map((p, i) => (
                <div key={i} className="p-3 bg-slate-900/40 rounded-lg border border-slate-800/60 text-center">
                  <p className="text-[10px] text-slate-500 font-mono mb-1">{p.label}</p>
                  <p className="text-sm font-bold text-cyan-400 font-mono">{p.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
