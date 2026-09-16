import React, { useState } from 'react';
import {
  Bell, Moon, Sun, ChevronDown, Wind, Waves,
  MapPin, FileText, UserCircle, Shield
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

  const severityColor = (s: string) =>
    s === 'HIGH' ? 'bg-[#EF4444]' : s === 'MEDIUM' ? 'bg-[#F59E0B]' : 'bg-[#10B981]';

  return (
    <div className={`h-[64px] border-b flex items-center px-4 gap-4 shrink-0 z-50 ${darkMode ? 'bg-[#070B12] border-[#1E293B]' : 'bg-[#F8FAFC] border-[#E2E8F0]'}`}>

      {/* LEFT: Branding */}
      <div className="flex items-center gap-3 shrink-0">
        <div className={`w-8 h-8 rounded flex items-center justify-center ${darkMode ? 'bg-[#0284C7]/20 border border-[#0284C7]/50' : 'bg-[#0369A1]/10 border border-[#0369A1]/30'}`}>
          <Shield className={`w-5 h-5 ${darkMode ? 'text-[#0284C7]' : 'text-[#0369A1]'}`} />
        </div>
        <div className="flex flex-col">
          <h1 className={`text-xs font-black tracking-widest flex items-center gap-2 ${darkMode ? 'text-[#F8FAFC]' : 'text-[#0F172A]'}`}>
            SLICKTRACE v2
            <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider border ${darkMode ? 'bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/20' : 'bg-[#DC2626]/10 text-[#DC2626] border-[#DC2626]/20'}`}>
              C4ISR MARITIME RECON
            </span>
          </h1>
          <p className={`text-[9px] font-mono tracking-wider uppercase mt-0.5 ${darkMode ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>
            Indian Coast Guard Surveillance Cell
          </p>
        </div>
      </div>

      {/* Spacer to push center to the center */}
      <div className="flex-1" />

      {/* CENTER: Incident Selector & Telemetry */}
      <div className="flex items-center gap-4 border-l border-r px-4 shrink-0" style={{ borderColor: darkMode ? '#1E293B' : '#E2E8F0' }}>
        
        {/* Incident Selector */}
        <div className="relative">
          <button
            onClick={() => setIncidentOpen(v => !v)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded border transition-colors min-w-[240px] ${darkMode ? 'bg-[#0F172A] border-[#1E293B] hover:border-[#0284C7]/50' : 'bg-white border-[#E2E8F0] hover:border-[#0369A1]/50'}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${severityColor(activeIncident.severity)} animate-pulse`} />
            <span className={`text-[11px] font-medium truncate flex-1 text-left ${darkMode ? 'text-[#F8FAFC]' : 'text-[#0F172A]'}`}>
              {activeIncident.id} ({activeIncident.name})
            </span>
            <ChevronDown className={`w-3.5 h-3.5 ${darkMode ? 'text-[#64748B]' : 'text-[#94A3B8]'} shrink-0`} />
          </button>
          
          {incidentOpen && (
            <div className={`absolute top-full left-0 mt-1 w-[320px] rounded-lg shadow-2xl z-50 overflow-hidden border ${darkMode ? 'bg-[#0F172A] border-[#1E293B]' : 'bg-white border-[#E2E8F0]'}`}>
              {DEMO_INCIDENTS.map(inc => (
                <button
                  key={inc.id}
                  onClick={() => { setActiveIncident(inc); setIncidentOpen(false); }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors ${activeIncident.id === inc.id ? (darkMode ? 'bg-[#0284C7]/10' : 'bg-[#0369A1]/5') : (darkMode ? 'hover:bg-[#1E293B]/50' : 'hover:bg-slate-50')}`}
                >
                  <span className={`w-2 h-2 rounded-full shrink-0`} style={{ backgroundColor: inc.color }} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-[11px] font-bold font-mono ${darkMode ? 'text-[#F8FAFC]' : 'text-[#0F172A]'}`}>{inc.id}</p>
                    <p className={`text-[10px] truncate ${darkMode ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>{inc.name} ({inc.oilType})</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Metocean Readout */}
        <div className="flex items-center gap-3">
          <div className={`flex flex-col items-end ${darkMode ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>
            <span className="flex items-center gap-1 text-[10px] font-mono">
              <MapPin className="w-3 h-3" />
              {metocean.lat.toFixed(4)}° N, {metocean.lon.toFixed(4)}° E
            </span>
          </div>
          <div className="flex flex-col items-start border-l pl-3" style={{ borderColor: darkMode ? '#1E293B' : '#E2E8F0' }}>
            <div className={`flex items-center gap-1 text-[10px] font-mono ${darkMode ? 'text-[#38BDF8]' : 'text-[#0369A1]'}`}>
              <Wind className="w-3 h-3" />
              <span>ERA5 10m: {metocean.windSpeed} m/s @ 245° (WSW)</span>
            </div>
            <div className={`flex items-center gap-1 text-[10px] font-mono mt-0.5 ${darkMode ? 'text-[#818CF8]' : 'text-[#4338CA]'}`}>
              <Waves className="w-3 h-3" />
              <span>INCOIS/CMEMS: {metocean.currentSpeed} kn @ 112° (ESE)</span>
            </div>
          </div>
        </div>

      </div>

      {/* Spacer to push right to the end */}
      <div className="flex-1" />

      {/* RIGHT: Actions */}
      <div className="flex items-center gap-3 shrink-0">
        
        {/* Dossier Button */}
        <button className={`flex items-center gap-1.5 px-3 py-1.5 rounded border transition-colors ${darkMode ? 'bg-[#0F172A] border-[#1E293B] hover:border-[#F59E0B]/50' : 'bg-white border-[#E2E8F0] hover:border-[#D97706]/50'}`}>
          <FileText className={`w-3.5 h-3.5 ${darkMode ? 'text-[#F59E0B]' : 'text-[#D97706]'}`} />
          <span className={`text-[10px] font-bold tracking-wide uppercase ${darkMode ? 'text-[#F8FAFC]' : 'text-[#0F172A]'}`}>
            Generate ISO 27037 Legal Dossier
          </span>
        </button>

        {/* Dark/Light Toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className={`p-1.5 rounded transition-colors border ${darkMode ? 'bg-[#0F172A] border-[#1E293B] hover:bg-[#1E293B]' : 'bg-white border-[#E2E8F0] hover:bg-slate-50'}`}
        >
          {darkMode
            ? <Moon className="w-4 h-4 text-[#94A3B8]" />
            : <Sun className="w-4 h-4 text-[#D97706]" />
          }
        </button>

        {/* User Role */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded border ${darkMode ? 'bg-[#10B981]/10 border-[#10B981]/20' : 'bg-[#059669]/10 border-[#059669]/20'}`}>
          <UserCircle className={`w-4 h-4 ${darkMode ? 'text-[#10B981]' : 'text-[#059669]'}`} />
          <div className="flex flex-col">
            <span className={`text-[10px] font-bold leading-none ${darkMode ? 'text-[#10B981]' : 'text-[#059669]'}`}>ICG Duty Officer</span>
            <span className={`text-[8px] leading-none mt-0.5 ${darkMode ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>Surveillance Desk</span>
          </div>
        </div>
        
      </div>

    </div>
  );
};
