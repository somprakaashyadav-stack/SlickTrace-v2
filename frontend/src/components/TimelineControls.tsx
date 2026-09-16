import React from 'react';
import { Play, Pause, SkipBack } from 'lucide-react';

interface TimelineControlsProps {
  currentTime: number; // 0 to 100 percentage
  setCurrentTime: (time: number) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
}

export const TimelineControls: React.FC<TimelineControlsProps> = ({
  currentTime,
  setCurrentTime,
  isPlaying,
  setIsPlaying
}) => {
  return (
    <div className="h-16 bg-navy-900 border-t border-slate-800 flex items-center px-6 shrink-0 gap-6">
      <div className="flex items-center gap-2">
        <button 
          onClick={() => { setIsPlaying(false); setCurrentTime(0); }}
          className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors"
        >
          <SkipBack className="w-4 h-4" />
        </button>
        <button 
          onClick={() => setIsPlaying(!isPlaying)}
          className="p-2 rounded-full bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-colors"
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
        </button>
      </div>

      <div className="flex-1 flex items-center gap-4">
        <span className="text-xs font-mono text-slate-400 w-12 text-right">-24h</span>
        <input 
          type="range" 
          min="0" 
          max="100" 
          value={currentTime}
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentTime(parseInt(e.target.value));
          }}
          className="flex-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
        />
        <span className="text-xs font-mono text-slate-400 w-12">NOW</span>
      </div>
    </div>
  );
};
