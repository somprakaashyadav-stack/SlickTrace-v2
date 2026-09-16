import React, { useState } from 'react';
import {
  Search, Bell, Moon, Sun, ChevronDown, Wind, Waves,
  MapPin, FileText, UserCircle
} from 'lucide-react';
import { Incident, MetoceanData, DEMO_INCIDENTS } from '../types/app';

interface TopBarProps {
  activeIncident: Incident;
  setActiveIncident: (incident: Incident) => void;
  metocean: MetoceanData;
  darkMode: boolean;
  setDarkMode: (v: boolean) => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  activeIncident,
  setActiveIncident,
  metocean,
  darkMode,
  setDarkMode,
}) => {
  const [incidentOpen, setIncidentOpen] = useState(false);
  const [notifications] = useState(2);

  const severityColor = (s: string) =>
    s === 'HIGH' ? 'bg-rose-500' : s === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <div className="h-10 bg-[#060b14] border-b border-slate-800/60 flex items-center px-3 gap-3 shrink-0 z-50">

      {/* Incident Selector */}
      <div className="relative">
        <button
          onClick={() => setIncidentOpen(v => !v)}
          className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-800/60 border border-slate-700/50 hover:border-cyan-500/30 transition-colors min-w-[200px]"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${severityColor(activeIncident.severity)} animate-pulse`} />
          <span className="text-[10px] font-medium text-slate-200 truncate flex-1 text-left">
            {activeIncident.id} · {activeIncident.name}
          </span>
          <ChevronDown className="w-3 h-3 text-slate-500 shrink-0" />
        </button>
        {incidentOpen && (
          <div className="absolute top-full left-0 mt-1 w-80 bg-[#0a101d] border border-slate-700 rounded-lg shadow-2xl z-50 overflow-hidden">
            {DEMO_INCIDENTS.map(inc => (
              <button
                key={inc.id}
                onClick={() => { setActiveIncident(inc); setIncidentOpen(false); }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-800/50 text-left transition-colors ${activeIncident.id === inc.id ? 'bg-cyan-500/10' : ''}`}
              >
                <span className={`w-2 h-2 rounded-full shrink-0`} style={{ backgroundColor: inc.color }} />
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-bold text-slate-200 font-mono">{inc.id}</p>
                  <p className="text-[9px] text-slate-400 truncate">{inc.name} ({inc.oilType})</p>
                </div>
                <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${inc.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>
                  {inc.severity}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Metocean Readout */}
      <div className="flex items-center gap-3 px-3 border-l border-slate-800">
        <div className="flex items-center gap-1 text-[10px] font-mono text-slate-300">
          <MapPin className="w-3 h-3 text-slate-500" />
          <span>{metocean.lat.toFixed(4)}°N, {metocean.lon.toFixed(4)}°E</span>
        </div>
        <div className="flex items-center gap-1 text-[10px] font-mono text-cyan-300">
          <Wind className="w-3 h-3 text-cyan-500" />
          <span>{metocean.windSpeed} m/s {metocean.windDir}</span>
        </div>
        <div className="flex items-center gap-1 text-[10px] font-mono text-blue-300">
          <Waves className="w-3 h-3 text-blue-500" />
          <span>{metocean.currentSpeed} kn {metocean.currentDir}</span>
        </div>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search */}
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800/60 border border-slate-700/40 w-40">
        <Search className="w-3 h-3 text-slate-500" />
        <input
          className="bg-transparent text-[10px] text-slate-300 placeholder-slate-600 outline-none w-full"
          placeholder="Search port, strait..."
        />
      </div>

      {/* Dossier Button */}
      <button className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-700/60 border border-slate-600/40 hover:border-cyan-500/40 transition-colors">
        <FileText className="w-3 h-3 text-slate-400" />
        <span className="text-[10px] text-slate-300 font-medium">Dossier</span>
      </button>

      {/* Dark/Light Toggle */}
      <button
        onClick={() => setDarkMode(!darkMode)}
        className="p-1.5 rounded hover:bg-slate-800 transition-colors"
      >
        {darkMode
          ? <Moon className="w-3.5 h-3.5 text-slate-400" />
          : <Sun className="w-3.5 h-3.5 text-amber-400" />
        }
      </button>

      {/* Notifications */}
      <button className="relative p-1.5 rounded hover:bg-slate-800 transition-colors">
        <Bell className="w-3.5 h-3.5 text-slate-400" />
        {notifications > 0 && (
          <span className="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-rose-500 rounded-full text-[7px] font-bold text-white flex items-center justify-center">
            {notifications}
          </span>
        )}
      </button>

      {/* User Role */}
      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-700/40 border border-slate-600/30">
        <UserCircle className="w-3.5 h-3.5 text-cyan-400" />
        <span className="text-[10px] font-bold text-slate-200">Duty Officer</span>
      </div>
    </div>
  );
};
