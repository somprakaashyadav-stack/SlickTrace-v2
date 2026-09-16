import React from 'react';
import { FinalRankingResponse, AISVesselTrack } from '../types';
import { ArrowUpCircle, ArrowDownCircle, MinusCircle, Navigation } from 'lucide-react';

interface LeaderboardPanelProps {
  ranking?: FinalRankingResponse;
  vessels: AISVesselTrack[];
  selectedMmsi: number | null;
  setSelectedMmsi: (mmsi: number) => void;
}

export const LeaderboardPanel: React.FC<LeaderboardPanelProps> = ({ ranking, vessels, selectedMmsi, setSelectedMmsi }) => {
  if (!ranking || ranking.rankings.length === 0) {
    return (
      <div className="w-80 bg-navy-950 border-r border-slate-800 flex flex-col items-center justify-center p-6 text-center shrink-0">
        <p className="text-xs text-slate-500 font-mono">Loading Leaderboard...</p>
      </div>
    );
  }

  const getVesselFlag = (mmsi: number) => {
    const vessel = vessels.find(v => v.mmsi === mmsi);
    return vessel?.flag || 'UNKN';
  };

  const getPriorityColor = (priority: string) => {
    if (priority.includes('HIGH')) return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    if (priority.includes('MEDIUM')) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  };

  return (
    <div className="w-[450px] bg-navy-950 border-r border-slate-800 flex flex-col shrink-0 overflow-hidden">
      <div className="p-4 border-b border-slate-800 bg-navy-900/50">
        <h2 className="text-sm font-bold text-slate-100 uppercase tracking-widest flex items-center gap-2">
          <Navigation className="w-4 h-4 text-cyan-400" />
          Suspect Leaderboard
        </h2>
        <p className="text-[10px] text-slate-400 font-mono mt-1">Unified Multi-Factor Correlation</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-navy-950 border-b border-slate-800 text-[10px] uppercase font-mono text-slate-500 z-10">
            <tr>
              <th className="p-3 font-medium whitespace-nowrap">Rank</th>
              <th className="p-3 font-medium">Vessel Info</th>
              <th className="p-3 font-medium text-center">Score</th>
              <th className="p-3 font-medium text-center">Priority</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {ranking.rankings.map(candidate => {
              const isSelected = selectedMmsi === candidate.mmsi;
              const flag = getVesselFlag(candidate.mmsi);
              
              return (
                <tr 
                  key={candidate.mmsi}
                  onClick={() => setSelectedMmsi(candidate.mmsi)}
                  className={`cursor-pointer hover:bg-slate-800/30 transition-colors ${isSelected ? 'bg-cyan-900/20' : ''}`}
                >
                  {/* Rank & Change */}
                  <td className="p-3 align-top">
                    <div className="flex flex-col items-center">
                      <span className={`text-lg font-black font-mono ${isSelected ? 'text-cyan-400' : 'text-slate-300'}`}>
                        #{candidate.rank}
                      </span>
                      <div className="flex items-center gap-1 mt-1" title="Rank Change from Initial to Final">
                        {candidate.rank_change > 0 ? (
                          <><ArrowUpCircle className="w-3 h-3 text-emerald-500" /><span className="text-[10px] text-emerald-500 font-mono">+{candidate.rank_change}</span></>
                        ) : candidate.rank_change < 0 ? (
                          <><ArrowDownCircle className="w-3 h-3 text-rose-500" /><span className="text-[10px] text-rose-500 font-mono">{candidate.rank_change}</span></>
                        ) : (
                          <><MinusCircle className="w-3 h-3 text-slate-600" /><span className="text-[10px] text-slate-500 font-mono">0</span></>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Vessel Info */}
                  <td className="p-3 align-top">
                    <div className="flex flex-col">
                      <span className={`font-bold text-xs ${isSelected ? 'text-slate-100' : 'text-slate-300'}`}>
                        {candidate.vessel_name}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono mt-0.5">
                        MMSI: {candidate.mmsi} | {flag}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono truncate max-w-[150px]">
                        {candidate.vessel_type}
                      </span>
                      
                      <div className="mt-2 text-[10px] flex gap-2">
                        <span className={`px-1.5 py-0.5 rounded border ${
                          candidate.ais_reliability === 'HIGH' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          AIS: {candidate.ais_reliability}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Score Breakdown */}
                  <td className="p-3 align-top text-center font-mono">
                    <div className="flex flex-col items-center">
                      <span className="text-sm font-bold text-cyan-400">{candidate.final_score}</span>
                      <div className="w-full bg-slate-800 rounded-full h-1 mt-1 mb-1 max-w-[50px]">
                        <div className="bg-cyan-500 h-1 rounded-full" style={{ width: `${candidate.final_score}%` }}></div>
                      </div>
                      <div className="text-[9px] text-slate-500 flex flex-col mt-1">
                        <span>Beh: {candidate.initial_score}</span>
                        <span>Phy: {candidate.physics_score}</span>
                      </div>
                    </div>
                  </td>

                  {/* Priority */}
                  <td className="p-3 align-top text-center">
                    <span className={`px-2 py-1 text-[9px] font-bold rounded border uppercase ${getPriorityColor(candidate.investigation_priority)}`}>
                      {candidate.investigation_priority.replace(' PRIORITY', '')}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
