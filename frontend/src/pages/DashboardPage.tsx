import React from 'react';
import { InvestigatorDashboard } from '../components/InvestigatorDashboard';
import { SpillSummary, DriftSimulation, AISVesselTrack, PhysicsVerificationResponse, FinalRankingResponse } from '../types';
import { Incident } from '../types/app';

interface DashboardPageProps {
  spill?: SpillSummary;
  drift?: DriftSimulation;
  vessels: AISVesselTrack[];
  physics?: PhysicsVerificationResponse;
  ranking?: FinalRankingResponse;
  activeIncident: Incident;
}

export const DashboardPage: React.FC<DashboardPageProps> = (props) => {
  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <div className="px-4 py-2 border-b border-slate-800/60 flex items-center gap-2">
        <span className="text-xs font-bold text-slate-300">Indian Ocean &amp; EEZ Maritime Surveillance</span>
        <span className="ml-2 px-2 py-0.5 rounded text-[9px] font-bold"
          style={{ backgroundColor: `${props.activeIncident.color}20`, color: props.activeIncident.color, border: `1px solid ${props.activeIncident.color}40` }}>
          {props.activeIncident.oilType}
        </span>
      </div>
      <div className="flex-1 overflow-hidden">
        <InvestigatorDashboard
          spill={props.spill}
          drift={props.drift}
          vessels={props.vessels}
          physics={props.physics}
          ranking={props.ranking}
        />
      </div>
    </div>
  );
};
