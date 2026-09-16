import React, { useState } from 'react';
import { ArrowUpCircle, ArrowDownCircle, MinusCircle, FileText, Layers, Loader2 } from 'lucide-react';
import { FinalRankingResponse, PhysicsVerificationResponse } from '../types';
import { PhysicsVerificationModal } from './PhysicsVerificationModal';
import { api } from '../services/api';

interface EvidencePanelProps {
  ranking?: FinalRankingResponse;
  physics?: PhysicsVerificationResponse;
  selectedMmsi: number | null;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ ranking, physics, selectedMmsi }) => {
  const [showPhysicsModal, setShowPhysicsModal] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExportDossier = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const report = await api.getEvidenceReport();

      // Enrich with current suspect context
      const exportData = {
        ...report,
        exported_at: new Date().toISOString(),
        selected_suspect: suspect,
        all_rankings: ranking?.rankings ?? [],
      };

      // Trigger browser download as JSON file
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `slicktrace-dossier-${report.incident_id ?? 'report'}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      setExportError('Export failed. Check backend connection.');
    } finally {
      setExporting(false);
    }
  };

  if (!ranking) {
    return (
      <div className="w-80 bg-navy-900 border-l border-slate-800 flex flex-col items-center justify-center p-6 text-center shrink-0">
        <Activity className="w-8 h-8 text-slate-700 animate-spin mb-4" />
        <p className="text-xs text-slate-500 font-mono">Initializing Forensics Engine...</p>
      </div>
    );
  }

  // If no specific vessel is selected, default to the top ranked
  const displayMmsi = selectedMmsi || ranking.rankings[0]?.mmsi;
  const suspect = ranking.rankings.find(r => r.mmsi === displayMmsi);

  if (!suspect) {
    return (
      <div className="w-80 bg-navy-900 border-l border-slate-800 flex items-center justify-center p-6 text-center shrink-0">
        <p className="text-xs text-slate-500 font-mono">No suspect data available.</p>
      </div>
    );
  }

  return (
    <div className="w-[400px] bg-navy-900 border-l border-slate-800 flex flex-col shrink-0 overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-navy-950/30">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold font-mono text-cyan-400">RANK #{suspect.rank}</span>
          <span className={`px-2 py-0.5 text-[10px] font-bold rounded font-mono ${
            suspect.investigation_priority === 'HIGH PRIORITY' 
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              : suspect.investigation_priority === 'MEDIUM PRIORITY'
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          }`}>
            {suspect.investigation_priority}
          </span>
        </div>
        <h2 className="text-lg font-black text-slate-100 uppercase tracking-wide">{suspect.vessel_name}</h2>
        <div className="flex justify-between mt-1 text-[11px] font-mono text-slate-400">
          <span>MMSI: {suspect.mmsi}</span>
          <span>{suspect.vessel_type}</span>
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Score Breakdown */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="text-slate-300">Composite Score:</span>
            <span className="text-cyan-400 font-bold text-lg">{suspect.final_score}/100</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mb-4">
            <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${suspect.final_score}%` }}></div>
          </div>
          
          <div className="grid grid-cols-2 gap-2 mt-4">
            <div className="p-3 bg-navy-950 rounded-lg border border-slate-800">
              <p className="text-[10px] text-slate-500 font-mono mb-1">AIS / BEHAVIOR</p>
              <p className="text-sm font-bold text-slate-200">{suspect.initial_score}</p>
            </div>
            <div className="p-3 bg-navy-950 rounded-lg border border-slate-800">
              <p className="text-[10px] text-slate-500 font-mono mb-1">PHYSICS VERIF</p>
              <p className="text-sm font-bold text-slate-200">{suspect.physics_score}</p>
            </div>
          </div>
        </div>

        {/* Rank Change */}
        <div className="p-4 rounded-xl bg-navy-950 border border-slate-800">
          <div className="flex items-center gap-2 mb-2">
            {suspect.rank_change > 0 ? (
              <ArrowUpCircle className="w-4 h-4 text-emerald-500" />
            ) : suspect.rank_change < 0 ? (
              <ArrowDownCircle className="w-4 h-4 text-rose-500" />
            ) : (
              <MinusCircle className="w-4 h-4 text-slate-500" />
            )}
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Verification Shift
            </span>
          </div>
          <p className="text-[11px] text-slate-400 italic leading-relaxed font-sans">
            {suspect.rank_change_explanation}
          </p>
        </div>

        {/* Evidence Lists */}
        <div className="space-y-4">
          <div>
            <h4 className="text-[10px] font-bold text-emerald-500 mb-2 uppercase tracking-wider">Corroborating Evidence</h4>
            <ul className="space-y-1">
              {suspect.evidence_for.map((ev, i) => (
                <li key={i} className="text-[11px] text-slate-300 flex items-start gap-2">
                  <span className="text-emerald-500 mt-0.5">+</span> {ev}
                </li>
              ))}
            </ul>
          </div>
          
          {suspect.evidence_against.length > 0 && (
            <div>
              <h4 className="text-[10px] font-bold text-rose-500 mb-2 uppercase tracking-wider">Inconsistent Evidence</h4>
              <ul className="space-y-1">
                {suspect.evidence_against.map((ev, i) => (
                  <li key={i} className="text-[11px] text-slate-400 flex items-start gap-2">
                    <span className="text-rose-500 mt-0.5">-</span> {ev}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {physics && physics.results.find(r => r.mmsi === suspect.mmsi) && (
            <div className="p-3 bg-navy-950 rounded-lg border border-purple-500/20">
              <h4 className="text-[10px] font-bold text-purple-400 mb-2 uppercase tracking-wider">Top Physics Scenario</h4>
              <div className="space-y-1 text-[10px] font-mono text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-500">Spatial Overlap:</span>
                  <span>{physics.results.find(r => r.mmsi === suspect.mmsi)?.metrics.spatial_overlap_pct.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Centroid Error:</span>
                  <span>{physics.results.find(r => r.mmsi === suspect.mmsi)?.metrics.centroid_error_km.toFixed(2)} km</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Timing Error:</span>
                  <span>{physics.results.find(r => r.mmsi === suspect.mmsi)?.metrics.timing_error_hours.toFixed(1)} hrs</span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2 mt-4">
          <button 
            onClick={() => setShowPhysicsModal(true)}
            className="w-full py-3 rounded-lg bg-purple-600 hover:bg-purple-500 text-slate-100 font-bold text-[10px] uppercase tracking-wider transition-colors flex flex-col justify-center items-center gap-1"
          >
            <Layers className="w-4 h-4" /> Physics Engine
          </button>
          <button
            onClick={handleExportDossier}
            disabled={exporting}
            className="w-full py-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 font-bold text-[10px] uppercase tracking-wider transition-colors flex flex-col justify-center items-center gap-1"
          >
            {exporting
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Exporting...</>
              : <><FileText className="w-4 h-4" /> Export Dossier</>
            }
          </button>
        </div>
        {exportError && (
          <p className="text-rose-400 text-[10px] font-mono mt-2 text-center">{exportError}</p>
        )}
      </div>

      {showPhysicsModal && physics && (
        <PhysicsVerificationModal 
          result={physics.results.find(r => r.mmsi === suspect.mmsi)!}
          candidate={suspect}
          onClose={() => setShowPhysicsModal(false)}
        />
      )}
    </div>
  );
};

// Add missing import for Activity icon
import { Activity } from 'lucide-react';
