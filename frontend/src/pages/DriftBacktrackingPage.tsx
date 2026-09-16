import React, { useState } from 'react';
import { Navigation2, ArrowRight } from 'lucide-react';
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

  const [particles, setParticles] = useState(1000);
  const [stokesDrag, setStokesDrag] = useState(3.5);
  const [diffusivity, setDiffusivity] = useState(10);

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-[#070B12]">
      {/* Page Header */}
      <div className="px-6 py-4 border-b border-[#1E293B] flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-lg font-black text-[#F8FAFC]">Lagrangian Hydrodynamic Drift Simulation</h1>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30">OpenDrift RK4</span>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#0284C7]/20 text-[#0284C7] border border-[#0284C7]/30">OpenOil</span>
          </div>
          <p className="text-xs text-[#94A3B8]">Backward Monte Carlo Dispersion driven by CMEMS Ocean Currents & ERA5 10m Wind Vectors</p>
        </div>
        <button
          onClick={() => navigate('/attribution')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0284C7] hover:bg-sky-500 text-white text-xs font-bold transition-colors"
        >
          4D AIS Attribution <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="p-6 grid grid-cols-2 gap-6 max-w-6xl">
        {/* Left Column: Physics & Sliders */}
        <div className="space-y-6">
          <div className="border border-[#1E293B] rounded-xl overflow-hidden bg-[#0F172A]">
            <div className="px-4 py-3 bg-[#070B12]/50 border-b border-[#1E293B]">
              <span className="text-[10px] font-bold text-[#94A3B8] uppercase tracking-widest">📐 Physical Back-Propagation Equation</span>
            </div>
            <div className="p-4 flex items-center justify-center bg-[#000000]/20">
              <span className="font-serif italic text-lg text-[#F8FAFC]">
                d<span className="font-bold">x</span>/dt = <span className="font-bold">u</span><sub>current</sub> + α <span className="font-bold">u</span><sub>wind</sub> + <span className="font-bold">u</span><sub>diffusion</sub>
              </span>
            </div>
          </div>

          <div className="border border-[#1E293B] rounded-xl overflow-hidden bg-[#0F172A]">
            <div className="px-4 py-3 bg-[#070B12]/50 border-b border-[#1E293B]">
              <span className="text-[10px] font-bold text-[#94A3B8] uppercase tracking-widest">⚙ Live Parameter Sliders</span>
            </div>
            <div className="p-5 space-y-5">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-[#94A3B8]">Particles (N)</span>
                  <span className="text-xs font-bold text-[#38BDF8] font-mono">{particles.toLocaleString()}</span>
                </div>
                <input type="range" min="500" max="2000" step="100" value={particles} onChange={e => setParticles(+e.target.value)} className="w-full h-1.5 accent-[#0284C7] bg-[#1E293B] rounded-full" />
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-[#94A3B8]">Stokes Drift Wind Drag (α)</span>
                  <span className="text-xs font-bold text-[#38BDF8] font-mono">{stokesDrag.toFixed(1)}%</span>
                </div>
                <input type="range" min="2.0" max="5.0" step="0.1" value={stokesDrag} onChange={e => setStokesDrag(+e.target.value)} className="w-full h-1.5 accent-[#0284C7] bg-[#1E293B] rounded-full" />
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-[#94A3B8]">Horizontal Diffusivity</span>
                  <span className="text-xs font-bold text-[#38BDF8] font-mono">{diffusivity} m²/s</span>
                </div>
                <input type="range" min="5" max="20" step="1" value={diffusivity} onChange={e => setDiffusivity(+e.target.value)} className="w-full h-1.5 accent-[#0284C7] bg-[#1E293B] rounded-full" />
              </div>
              <div className="pt-2 border-t border-[#1E293B]">
                <span className="text-xs text-[#94A3B8]">Integration Solver: <span className="font-bold text-[#F8FAFC]">Runge-Kutta 4th Order (RK4)</span></span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Outputs & Weathering */}
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-[#0F172A] rounded-xl border border-[#1E293B]">
              <p className="text-[10px] text-[#94A3B8] font-mono mb-2 uppercase">50% Centroid Coordinates</p>
              <p className="text-xl font-black text-[#38BDF8] font-mono">
                {origin ? `${origin.Y0.toFixed(2)}°N, ${origin.X0.toFixed(2)}°E` : `18.62°N, 71.18°E`}
              </p>
            </div>
            <div className="p-4 bg-[#0F172A] rounded-xl border border-[#1E293B]">
              <p className="text-[10px] text-[#94A3B8] font-mono mb-2 uppercase">Estimated Discharge Time Window</p>
              <p className="text-lg font-black text-[#F59E0B] font-mono">
                T - 21h to T - 24h
              </p>
            </div>
            <div className="col-span-2 p-4 bg-[#0F172A] rounded-xl border border-[#1E293B] flex items-center justify-between">
              <div>
                <p className="text-[10px] text-[#94A3B8] font-mono mb-1 uppercase">Dispersion Area</p>
                <p className="text-xl font-black text-[#10B981] font-mono">
                  {(68.4 + (diffusivity - 10) * 2.1 + (particles - 1000) * 0.01).toFixed(1)} km²
                </p>
              </div>
              <Navigation2 className="w-8 h-8 text-[#1E293B]" />
            </div>
          </div>

          <div className="border border-[#1E293B] rounded-xl overflow-hidden bg-[#0F172A]">
            <div className="px-4 py-3 bg-[#070B12]/50 border-b border-[#1E293B]">
              <span className="text-[10px] font-bold text-[#94A3B8] uppercase tracking-widest">📉 OpenOil Weathering Degradation Chart</span>
            </div>
            <div className="p-5">
              <p className="text-xs text-[#94A3B8] mb-4">72h Mass-Balance Trajectory</p>
              {/* Stacked area chart visualization (CSS Mock) */}
              <div className="h-40 w-full relative flex items-end overflow-hidden rounded border border-[#1E293B] bg-[#070B12]">
                <div className="absolute inset-0 flex">
                  {/* Fake area graph layers */}
                  <div className="w-full h-full relative">
                    {/* Surface Emulsion (48%) */}
                    <div className="absolute bottom-0 left-0 right-0 bg-[#0284C7]/80" style={{ height: '48%', clipPath: 'polygon(0 100%, 0 20%, 25% 10%, 50% 15%, 75% 5%, 100% 0, 100% 100%)' }} />
                    {/* Natural Dispersion (16%) */}
                    <div className="absolute left-0 right-0 bg-[#10B981]/80" style={{ bottom: '48%', height: '16%', clipPath: 'polygon(0 100%, 0 20%, 25% 40%, 50% 25%, 75% 55%, 100% 30%, 100% 100%)' }} />
                    {/* Evaporation (36%) */}
                    <div className="absolute left-0 right-0 bg-[#8B5CF6]/80" style={{ bottom: '64%', height: '36%', clipPath: 'polygon(0 100%, 0 0, 25% 20%, 50% 10%, 75% 40%, 100% 20%, 100% 100%)' }} />
                  </div>
                </div>
                {/* Labels */}
                <div className="absolute inset-0 flex flex-col justify-between p-2 pointer-events-none">
                  <div className="flex justify-between items-start w-full">
                    <span className="text-[10px] font-bold text-white drop-shadow-md">Evaporation: 36%</span>
                  </div>
                  <div className="flex justify-between items-center w-full h-full">
                    <span className="text-[10px] font-bold text-white drop-shadow-md mt-6">Natural Dispersion: 16%</span>
                  </div>
                  <div className="flex justify-between items-end w-full">
                    <span className="text-[10px] font-bold text-white drop-shadow-md mb-2">Surface Emulsion: 48%</span>
                    <span className="text-[10px] font-bold text-white drop-shadow-md">T - 72h</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
