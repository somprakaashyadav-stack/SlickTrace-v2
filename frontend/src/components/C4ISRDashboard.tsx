import React, { useState } from 'react';
import { SpillSummary, DriftSimulation, AISVesselTrack, PhysicsVerificationResponse, FinalRankingResponse } from '../types';
import { Incident, MetoceanData } from '../types/app';
import { C4ISRHeader } from './C4ISRHeader';
import { PanelAWorkbench } from './PanelAWorkbench';
import { PanelBMap } from './PanelBMap';
import { PanelCAttribution } from './PanelCAttribution';
import { PanelDEvidence } from './PanelDEvidence';

interface C4ISRDashboardProps {
  spill?: SpillSummary;
  drift?: DriftSimulation;
  vessels: AISVesselTrack[];
  physics?: PhysicsVerificationResponse;
  ranking?: FinalRankingResponse;
  activeIncident: Incident;
  setActiveIncident: (inc: Incident) => void;
  metocean: MetoceanData;
}

export const C4ISRDashboard: React.FC<C4ISRDashboardProps> = ({
  spill, drift, vessels, physics, ranking, activeIncident, setActiveIncident, metocean
}) => {
  const [currentTime, setCurrentTime] = useState<number>(100);
  const [selectedMmsi, setSelectedMmsi] = useState<number | null>(null);

  // Default to top candidate if not selected
  React.useEffect(() => {
    if (ranking?.rankings?.length && selectedMmsi === null) {
      setSelectedMmsi(ranking.rankings[0].mmsi);
    }
  }, [ranking, selectedMmsi]);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#02060d] text-slate-200 overflow-hidden font-sans">
      
      {/* HEADER */}
      <C4ISRHeader 
        activeIncident={activeIncident} 
        setActiveIncident={setActiveIncident} 
        metocean={metocean} 
      />

      {/* 4-PANEL GRID LAYOUT */}
      <div className="flex-1 flex overflow-hidden p-2 gap-2">
        
        {/* LEFT COLUMN: Panel A (Top) & Panel D (Bottom) */}
        <div className="w-[380px] flex flex-col gap-2 shrink-0">
          <div className="flex-[4] min-h-0 bg-slate-900/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col shadow-2xl">
            <PanelAWorkbench />
          </div>
          <div className="flex-[3] min-h-0 bg-slate-900/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col shadow-2xl">
            <PanelDEvidence 
              ranking={ranking} 
              physics={physics} 
              selectedMmsi={selectedMmsi} 
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Panel B (Top/Map) & Panel C (Bottom) */}
        <div className="flex-1 flex flex-col gap-2 min-w-0">
          <div className="flex-[5] min-h-0 bg-slate-900/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col relative shadow-2xl">
            <PanelBMap 
              spill={spill}
              drift={drift}
              vessels={vessels}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              selectedMmsi={selectedMmsi}
              setSelectedMmsi={setSelectedMmsi}
            />
          </div>
          <div className="flex-[3] min-h-0 bg-slate-900/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col shadow-2xl">
            <PanelCAttribution 
              ranking={ranking}
              vessels={vessels}
              physics={physics}
              selectedMmsi={selectedMmsi}
              setSelectedMmsi={setSelectedMmsi}
            />
          </div>
        </div>

      </div>
    </div>
  );
};
