import React from 'react';
import { Incident, MetoceanData, DEMO_INCIDENTS } from '../types/app';
import { Shield, Map, Wind, Droplets, Lock, ChevronDown, FileKey } from 'lucide-react';

interface C4ISRHeaderProps {
  activeIncident: Incident;
  setActiveIncident: (inc: Incident) => void;
  metocean: MetoceanData;
}

export const C4ISRHeader: React.FC<C4ISRHeaderProps> = ({ activeIncident, setActiveIncident, metocean }) => {
  return (
    <div className="h-14 bg-[#0a111a] border-b border-slate-800 flex items-center px-4 justify-between shrink-0">
      
      {/* BRANDING */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-cyan-950 border border-cyan-500/50 flex items-center justify-center">
          <Shield className="w-5 h-5 text-cyan-400" />
        </div>
        <div className="flex flex-col">
          <h1 className="text-xs font-black text-slate-100 tracking-widest flex items-center gap-2">
            SLICKTRACE <span className="text-cyan-500">v2</span> 
            <span className="text-[10px] px-1.5 py-0.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded uppercase tracking-wider">
              C4ISR MARITIME RECONNAISSANCE
            </span>
          </h1>
          <p className="text-[9px] text-slate-500 font-mono tracking-wider uppercase">Indian Coast Guard Surveillance Cell · Sector: Mumbai High</p>
        </div>
      </div>

      {/* CONTROLS */}
      <div className="flex items-center gap-4">
        
        {/* Incident Selector */}
        <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 px-3 py-1.5 rounded">
          <Map className="w-3.5 h-3.5 text-slate-400" />
          <select 
            className="bg-transparent text-[10px] font-bold text-slate-200 outline-none uppercase tracking-wider appearance-none cursor-pointer"
            value={activeIncident.id}
            onChange={(e) => {
              const inc = DEMO_INCIDENTS.find(i => i.id === e.target.value);
              if (inc) setActiveIncident(inc);
            }}
          >
            {DEMO_INCIDENTS.map(inc => (
              <option key={inc.id} value={inc.id} className="bg-slate-900">
                {inc.id} — {inc.location}
              </option>
            ))}
          </select>
          <ChevronDown className="w-3 h-3 text-slate-500" />
        </div>

        {/* Sector Lock */}
        <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded text-[10px] font-bold text-emerald-400 cursor-pointer hover:bg-emerald-500/20 transition-colors">
          <Lock className="w-3 h-3" />
          SECTOR LOCK
        </div>

        {/* Telemetry */}
        <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
          <div className="flex flex-col items-end">
            <span className="text-[9px] text-slate-500 font-mono uppercase">ERA5 10m Wind</span>
            <span className="text-[10px] font-bold text-sky-400 flex items-center gap-1">
              <Wind className="w-3 h-3" /> {metocean.windSpeed} kt @ {metocean.windDir}°
            </span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[9px] text-slate-500 font-mono uppercase">INCOIS CMEMS</span>
            <span className="text-[10px] font-bold text-blue-400 flex items-center gap-1">
              <Droplets className="w-3 h-3" /> {metocean.currentSpeed} kt @ {metocean.currentDir}°
            </span>
          </div>
        </div>

        {/* ISO 27037 Manifest */}
        <div className="flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/30 px-3 py-1.5 rounded text-[10px] font-bold text-indigo-400 cursor-pointer hover:bg-indigo-500/20 transition-colors ml-2">
          <FileKey className="w-3 h-3" />
          ISO 27037 MANIFEST
        </div>

      </div>
    </div>
  );
};
