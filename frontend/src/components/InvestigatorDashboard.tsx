import React, { useState, useEffect } from 'react';
import { TopStatusBar } from './TopStatusBar';
import { MapEngine } from './MapEngine';
import { TimelineControls } from './TimelineControls';
import { EvidencePanel } from './EvidencePanel';
import { LeaderboardPanel } from './LeaderboardPanel';
import { SpillSummary, DriftSimulation, AISVesselTrack, PhysicsVerificationResponse, FinalRankingResponse } from '../types';

interface InvestigatorDashboardProps {
  spill?: SpillSummary;
  drift?: DriftSimulation;
  vessels: AISVesselTrack[];
  physics?: PhysicsVerificationResponse;
  ranking?: FinalRankingResponse;
}

export const InvestigatorDashboard: React.FC<InvestigatorDashboardProps> = ({
  spill,
  drift,
  vessels,
  physics,
  ranking
}) => {
  const [currentTime, setCurrentTime] = useState<number>(100);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedMmsi, setSelectedMmsi] = useState<number | null>(null);

  // Default to top ranked suspect if available and none selected
  useEffect(() => {
    if (ranking?.rankings?.length && selectedMmsi === null) {
      setSelectedMmsi(ranking.rankings[0].mmsi);
    }
  }, [ranking, selectedMmsi]);

  // Timeline playback loop
  useEffect(() => {
    let interval: number;
    if (isPlaying) {
      interval = window.setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= 100) {
            setIsPlaying(false);
            return 100;
          }
          return prev + 0.5; // Smooth progression
        });
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div className="flex flex-col h-full w-full bg-navy-950 overflow-hidden">
      {/* Top Status Bar */}
      <TopStatusBar spill={spill} ranking={ranking} />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left: Leaderboard Panel */}
        <LeaderboardPanel 
          ranking={ranking}
          vessels={vessels}
          selectedMmsi={selectedMmsi}
          setSelectedMmsi={setSelectedMmsi}
        />

        {/* Center: Map */}
        <div className="flex-1 relative bg-navy-900 border-r border-slate-800">
          <MapEngine 
            spill={spill}
            drift={drift}
            vessels={vessels}
            physics={physics}
            currentTime={currentTime}
            selectedMmsi={selectedMmsi}
            setSelectedMmsi={setSelectedMmsi}
          />
        </div>

        {/* Right: Evidence Panel */}
        <EvidencePanel 
          ranking={ranking}
          physics={physics}
          selectedMmsi={selectedMmsi}
        />
      </div>

      {/* Bottom: Timeline Controls */}
      <TimelineControls 
        currentTime={currentTime}
        setCurrentTime={setCurrentTime}
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
      />
    </div>
  );
};
