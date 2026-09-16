import React from 'react';
import { Activity, ShieldCheck, MapPin, Target, Clock, ShieldAlert } from 'lucide-react';
import { SpillSummary, FinalRankingResponse } from '../types';

interface TopStatusBarProps {
  spill?: SpillSummary;
  ranking?: FinalRankingResponse;
}

export const TopStatusBar: React.FC<TopStatusBarProps> = ({ spill, ranking }) => {
  const topCandidate = ranking?.rankings?.[0];

  return (
    <div className="h-14 bg-navy-900 border-b border-slate-800 flex items-center px-4 shrink-0 font-mono text-xs overflow-x-auto whitespace-nowrap">
      
      {/* Brand / Title */}
      <div className="flex items-center gap-2 mr-8 text-cyan-400 font-bold border-r border-slate-800 pr-6 py-1">
        <Activity className="w-4 h-4" />
        <span className="tracking-widest">SLICKTRACE V2</span>
      </div>

      <div className="flex items-center gap-6 text-slate-300">
        <div className="flex items-center gap-2">
          <span className="text-slate-500">SCENE ID:</span>
          <span className="font-bold text-slate-200">{spill?.scene_id || 'PENDING'}</span>
        </div>

        <div className="w-px h-4 bg-slate-800"></div>

        <div className="flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-slate-500">CONFIDENCE:</span>
          <span className="font-bold text-emerald-400">{spill?.confidence_score}%</span>
        </div>

        <div className="w-px h-4 bg-slate-800"></div>

        <div className="flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-500">CENTER:</span>
          <span>{spill?.center_lat.toFixed(4)}°N, {spill?.center_lon.toFixed(4)}°E</span>
        </div>

        <div className="w-px h-4 bg-slate-800"></div>

        <div className="flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-500">EST T0 WINDOW:</span>
          <span>{spill?.detection_time ? new Date(new Date(spill.detection_time).getTime() - 24*3600*1000).toISOString().split('T')[1].substring(0,5) : 'N/A'} - {spill?.detection_time?.split('T')[1].substring(0,5) || 'N/A'}</span>
        </div>

        <div className="w-px h-4 bg-slate-800"></div>

        <div className="flex items-center gap-2">
          <Target className="w-3.5 h-3.5 text-rose-400" />
          <span className="text-slate-500">TOP MATCH:</span>
          <span className="font-bold text-rose-400">{topCandidate ? topCandidate.vessel_name : 'ANALYZING...'}</span>
        </div>

        <div className="w-px h-4 bg-slate-800"></div>

        <div className="flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-500">PHYSICS:</span>
          <span className="font-bold text-purple-400">{topCandidate ? (topCandidate.physics_score > 70 ? 'VERIFIED' : 'FAILED') : 'PENDING'}</span>
        </div>
      </div>
    </div>
  );
};
