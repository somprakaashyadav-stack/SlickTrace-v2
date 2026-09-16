import React from 'react';
import { SpillSummary, DriftSimulation, AISVesselTrack } from '../types';
import { MapEngine } from './MapEngine';
import { Clock, Navigation, History, Waves } from 'lucide-react';

interface PanelBMapProps {
  spill?: SpillSummary;
  drift?: DriftSimulation;
  vessels: AISVesselTrack[];
  currentTime: number;
  setCurrentTime: (t: number | ((prev: number) => number)) => void;
  selectedMmsi: number | null;
  setSelectedMmsi: (mmsi: number) => void;
}

export const PanelBMap: React.FC<PanelBMapProps> = ({
  spill, drift, vessels, currentTime, setCurrentTime, selectedMmsi, setSelectedMmsi
}) => {
  return (
    <div className="h-full flex flex-col font-sans relative">
      {/* Header overlay over map */}
      <div className="absolute top-0 left-0 right-0 z-10 p-2 bg-gradient-to-b from-slate-900/90 to-transparent flex items-center justify-between pointer-events-none">
        <h2 className="text-[10px] font-black text-slate-100 uppercase tracking-widest flex items-center gap-1.5 drop-shadow-md">
          <Navigation className="w-3.5 h-3.5 text-blue-400" />
          4D Hydrodynamic Canvas & Interactive Timeline
        </h2>
        <div className="flex gap-2 text-[8px] font-mono font-bold">
          <span className="text-blue-400 bg-blue-900/40 px-1.5 py-0.5 rounded border border-blue-500/30 backdrop-blur-sm">N=1,000 Particles</span>
          <span className="text-amber-400 bg-amber-900/40 px-1.5 py-0.5 rounded border border-amber-500/30 backdrop-blur-sm">T+24h Booming</span>
        </div>
      </div>

      {/* Map Engine */}
      <div className="flex-1 bg-slate-950 relative">
        <MapEngine 
          spill={spill}
          drift={drift}
          vessels={vessels}
          currentTime={currentTime}
          selectedMmsi={selectedMmsi}
          setSelectedMmsi={setSelectedMmsi}
        />
      </div>

      {/* 4D Scrub Bar */}
      <div className="h-14 bg-slate-900/90 border-t border-slate-800 p-2 flex items-center gap-4 z-20 shrink-0">
        <div className="flex flex-col items-center shrink-0">
          <span className="text-[9px] font-bold text-amber-500 uppercase flex items-center gap-1"><History className="w-3 h-3"/> T-72h</span>
          <span className="text-[7px] text-slate-500 font-mono">Discharge Window</span>
        </div>
        
        <div className="flex-1 flex flex-col justify-center relative">
          <input 
            type="range"
            min={0}
            max={100}
            value={currentTime}
            onChange={(e) => setCurrentTime(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 hover:accent-cyan-400 focus:outline-none"
          />
          <div className="absolute -top-1 w-full flex justify-between px-1 pointer-events-none">
            {[0, 25, 50, 75, 100].map(tick => (
              <div key={tick} className="w-0.5 h-3.5 bg-slate-600 rounded-full" />
            ))}
          </div>
        </div>
        
        <div className="flex flex-col items-center shrink-0">
          <span className="text-[9px] font-bold text-cyan-400 uppercase flex items-center gap-1"><Clock className="w-3 h-3"/> T0</span>
          <span className="text-[7px] text-slate-500 font-mono">Satellite Detection</span>
        </div>
      </div>
    </div>
  );
};
