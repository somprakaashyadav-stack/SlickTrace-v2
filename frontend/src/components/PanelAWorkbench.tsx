import React from 'react';
import { Satellite, Radio, Cpu, Network, CheckSquare, Droplet, Activity, UploadCloud } from 'lucide-react';

export const PanelAWorkbench: React.FC = () => {
  return (
    <div className="h-full flex flex-col font-sans">
      <div className="p-2 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
        <h2 className="text-[10px] font-black text-slate-100 uppercase tracking-widest flex items-center gap-1.5">
          <Satellite className="w-3.5 h-3.5 text-cyan-400" />
          Multi-Modal Ingestion & Spectral Workbench
        </h2>
        <span className="text-[8px] font-mono text-emerald-400 bg-emerald-500/10 px-1 py-0.5 rounded border border-emerald-500/20">LIVE INGENT</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-4 custom-scrollbar">
        
        {/* API Bridges */}
        <div>
          <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-1">Dual Gateway Ingestion</h3>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-950 border border-slate-800 rounded p-2 flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-200 flex items-center gap-1"><Network className="w-3 h-3 text-blue-400"/> Copernicus</span>
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />
              </div>
              <span className="text-[8px] text-slate-500 font-mono">Sentinel-1 C-SAR / Sentinel-2</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded p-2 flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-200 flex items-center gap-1"><Radio className="w-3 h-3 text-orange-400"/> ISRO Bhoonidhi</span>
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />
              </div>
              <span className="text-[8px] text-slate-500 font-mono">EOS-04 / NISAR L+S Band</span>
            </div>
          </div>
        </div>

        {/* SAR NRCS Transect */}
        <div>
          <div className="flex justify-between items-end mb-2 border-b border-slate-800 pb-1">
            <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">SAR NRCS Transect (VV Pol)</h3>
            <span className="text-[8px] font-mono text-cyan-500">Δσ₀ ≈ -8.4 dB</span>
          </div>
          <div className="h-16 bg-slate-950 border border-slate-800 rounded relative overflow-hidden flex items-end">
            <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(90deg, transparent 95%, #334155 100%)', backgroundSize: '20px 100%' }}></div>
            <svg viewBox="0 0 100 40" className="w-full h-full text-cyan-500 drop-shadow-[0_0_3px_rgba(6,182,212,0.8)]" preserveAspectRatio="none">
              <path d="M0 10 Q 15 12 30 10 T 40 30 Q 50 35 60 30 T 70 10 Q 85 8 100 10" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <div className="absolute top-1 right-2 text-[8px] font-mono text-slate-400">Capillary Damping Confirmed</div>
          </div>
        </div>

        {/* Look-alike Rejection */}
        <div>
          <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-1">Multi-Modal Look-Alike Rejection</h3>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between bg-slate-950/50 p-1.5 rounded border border-slate-800/50">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-3 h-3 text-emerald-500" />
                <span className="text-[10px] text-slate-300">Biogenic Rejection (FAI / OLCI)</span>
              </div>
              <span className="text-[8px] font-mono text-emerald-600 bg-emerald-500/10 px-1 rounded">CLEARED</span>
            </div>
            <div className="flex items-center justify-between bg-slate-950/50 p-1.5 rounded border border-slate-800/50">
              <div className="flex items-center gap-2">
                <Droplet className="w-3 h-3 text-cyan-500" />
                <span className="text-[10px] text-slate-300">SWIR Hydrocarbon Emulsion</span>
              </div>
              <span className="text-[8px] font-mono text-cyan-600 bg-cyan-500/10 px-1 rounded">MATCH</span>
            </div>
            <div className="flex items-center justify-between bg-slate-950/50 p-1.5 rounded border border-slate-800/50">
              <div className="flex items-center gap-2">
                <Activity className="w-3 h-3 text-indigo-400" />
                <span className="text-[10px] text-slate-300">ROI-Restricted Super-Resolution</span>
              </div>
              <span className="text-[8px] font-mono text-indigo-400 bg-indigo-500/10 px-1 rounded">ACTIVE</span>
            </div>
          </div>
        </div>

        {/* WASM ONNX Triage */}
        <div className="mt-auto">
          <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-1 flex items-center gap-1">
            <Cpu className="w-3 h-3 text-purple-400" /> Client-Side Edge Triage
          </h3>
          <div className="border border-dashed border-slate-700 bg-slate-950/50 rounded flex flex-col items-center justify-center py-4 cursor-pointer hover:bg-slate-900 transition-colors">
            <UploadCloud className="w-5 h-5 text-slate-500 mb-1" />
            <span className="text-[9px] text-slate-400 uppercase font-bold tracking-wider">Drag & Drop .TIF</span>
            <span className="text-[8px] text-slate-600 font-mono">WASM / ONNX Zero-Latency Inference</span>
          </div>
        </div>

      </div>
    </div>
  );
};
