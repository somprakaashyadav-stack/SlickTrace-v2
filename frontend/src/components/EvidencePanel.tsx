import React, { useState } from 'react';
import { ArrowUpCircle, ArrowDownCircle, MinusCircle, FileText, Layers, Loader2 } from 'lucide-react';
import { FinalRankingResponse, PhysicsVerificationResponse } from '../types';
import { PhysicsVerificationModal } from './PhysicsVerificationModal';
import { api } from '../services/api';
import jsPDF from 'jspdf';

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
      const rankings = ranking?.rankings ?? [];
      const now = new Date();

      // ── Init PDF ──────────────────────────────────────────────────────────
      const doc = new jsPDF({ unit: 'mm', format: 'a4' });
      const W = 210; // A4 width
      let y = 0;

      const addPage = () => { doc.addPage(); y = 15; };
      const checkY = (needed: number) => { if (y + needed > 275) addPage(); };

      // ── Helper: section header ────────────────────────────────────────────
      const sectionHeader = (title: string) => {
        checkY(12);
        doc.setFillColor(6, 11, 20);
        doc.rect(14, y, W - 28, 8, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(56, 189, 248); // cyan-400
        doc.text(title, 18, y + 5.5);
        y += 12;
      };

      const field = (label: string, value: string, indent = 18) => {
        checkY(7);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(148, 163, 184); // slate-400
        doc.text(label, indent, y);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(226, 232, 240); // slate-200
        doc.text(value, indent + 45, y);
        y += 6;
      };

      // ── PAGE 1 HEADER ─────────────────────────────────────────────────────
      // Dark banner
      doc.setFillColor(6, 11, 20);
      doc.rect(0, 0, W, 40, 'F');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(20);
      doc.setTextColor(56, 189, 248);
      doc.text('SLICKTRACE v2', 14, 16);

      doc.setFontSize(9);
      doc.setTextColor(100, 116, 139); // slate-500
      doc.text('Maritime Oil Spill Forensic Intelligence Platform', 14, 23);

      doc.setFontSize(8);
      doc.setTextColor(244, 63, 94); // rose
      doc.text('CONFIDENTIAL — MARPOL ENFORCEMENT DOSSIER', 14, 30);

      // Dossier ref top-right
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7);
      doc.setTextColor(100, 116, 139);
      doc.text(`Ref: ${report.dossier_reference ?? 'N/A'}`, W - 14, 16, { align: 'right' });
      doc.text(`Generated: ${now.toUTCString()}`, W - 14, 22, { align: 'right' });

      y = 48;

      // ── INCIDENT METADATA ─────────────────────────────────────────────────
      sectionHeader('01  INCIDENT METADATA');
      field('Incident ID', report.incident_id ?? 'N/A');
      field('Dossier Reference', report.dossier_reference ?? 'N/A');
      field('Verification Status', report.verification_status ?? 'N/A');
      field('Generated At', report.generated_at ?? now.toISOString());
      field('Exported At', now.toISOString());

      // ── SPILL SUMMARY ─────────────────────────────────────────────────────
      sectionHeader('02  DETECTED SPILL SUMMARY');
      const spill = report.spill_summary;
      if (spill) {
        field('Scene ID', spill.scene_id ?? 'N/A');
        field('Satellite', spill.satellite ?? 'N/A');
        field('Detection Time', spill.detection_time ?? 'N/A');
        field('Center Coordinates', `${spill.center_lat?.toFixed(4)}°N, ${spill.center_lon?.toFixed(4)}°E`);
        field('Area', `${spill.area_sq_km?.toFixed(2)} km²`);
        field('Est. Volume', `${spill.estimated_volume_m3?.toFixed(0)} m³`);
        field('Confidence Score', `${((spill.confidence_score ?? 0) * 100).toFixed(1)}%`);
      } else {
        doc.setFontSize(8); doc.setTextColor(148,163,184);
        doc.text('Spill summary unavailable.', 18, y); y += 6;
      }

      // ── DRIFT PHYSICS ORIGIN ──────────────────────────────────────────────
      sectionHeader('03  DRIFT PHYSICS — ESTIMATED ORIGIN');
      const drift = report.drift_physics_summary;
      if (drift) {
        field('Origin Centroid', `${drift.center_lat?.toFixed(4)}°N, ${drift.center_lon?.toFixed(4)}°E`);
        field('Est. Release Time', drift.estimated_release_time ?? 'N/A');
        field('Major Axis', `${drift.major_axis_km?.toFixed(2)} km`);
        field('Minor Axis', `${drift.minor_axis_km?.toFixed(2)} km`);
        field('Orientation', `${drift.orientation_deg?.toFixed(1)}°`);
      } else {
        doc.setFontSize(8); doc.setTextColor(148,163,184);
        doc.text('Drift physics summary unavailable.', 18, y); y += 6;
      }

      // ── SUSPECT RANKINGS ──────────────────────────────────────────────────
      sectionHeader('04  SUSPECT VESSEL RANKINGS');

      // Table header
      checkY(10);
      doc.setFillColor(15, 23, 42);
      doc.rect(14, y, W - 28, 7, 'F');
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(7);
      doc.setTextColor(100, 116, 139);
      const cols = [18, 28, 75, 120, 145, 165, 185];
      ['#', 'MMSI', 'VESSEL', 'TYPE', 'SCORE', 'PHYSICS', 'PRIORITY'].forEach((h, i) => {
        doc.text(h, cols[i], y + 5);
      });
      y += 9;

      rankings.forEach((r, idx) => {
        checkY(8);
        if (idx % 2 === 0) {
          doc.setFillColor(10, 16, 29);
          doc.rect(14, y - 1, W - 28, 7, 'F');
        }
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7);
        // rank color
        const rankColor: [number,number,number] = r.rank === 1 ? [244,63,94] : r.rank === 2 ? [251,191,36] : [100,116,139];
        doc.setTextColor(...rankColor);
        doc.text(`#${r.rank}`, cols[0], y + 4);
        doc.setTextColor(226, 232, 240);
        doc.text(String(r.mmsi), cols[1], y + 4);
        doc.text(r.vessel_name?.substring(0, 22) ?? '', cols[2], y + 4);
        doc.text(r.vessel_type?.substring(0, 18) ?? '', cols[3], y + 4);
        doc.text(String(r.final_score), cols[4], y + 4);
        doc.text(String(r.physics_score), cols[5], y + 4);
        // priority badge color
        const pColor: [number,number,number] = r.investigation_priority?.includes('HIGH')
          ? [244,63,94] : r.investigation_priority?.includes('MEDIUM')
          ? [251,191,36] : [52,211,153];
        doc.setTextColor(...pColor);
        doc.text(r.investigation_priority?.replace(' PRIORITY','') ?? '', cols[6], y + 4);
        y += 7;
      });

      y += 4;

      // ── PRIME SUSPECT DEEP-DIVE ───────────────────────────────────────────
      const top = rankings[0];
      if (top) {
        sectionHeader('05  PRIME SUSPECT — FULL EVIDENCE PROFILE');
        field('Vessel Name', top.vessel_name ?? 'N/A');
        field('MMSI', String(top.mmsi));
        field('Type', top.vessel_type ?? 'N/A');
        field('AIS Reliability', top.ais_reliability ?? 'N/A');
        field('Initial Score', String(top.initial_score));
        field('Physics Score', String(top.physics_score));
        field('Final Score', `${top.final_score}/100`);
        field('Rank Change', top.rank_change > 0 ? `+${top.rank_change}` : String(top.rank_change));
        field('Investigation Priority', top.investigation_priority ?? 'N/A');

        y += 2;
        // Evidence for
        checkY(10);
        doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.setTextColor(52, 211, 153);
        doc.text('CORROBORATING EVIDENCE', 18, y); y += 6;
        doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5); doc.setTextColor(203, 213, 225);
        (top.evidence_for ?? []).forEach(ev => {
          checkY(6);
          doc.setTextColor(52, 211, 153); doc.text('+', 18, y);
          doc.setTextColor(203, 213, 225);
          const lines = doc.splitTextToSize(ev, W - 44);
          doc.text(lines, 23, y);
          y += lines.length * 5 + 1;
        });

        y += 2;
        // Evidence against
        if ((top.evidence_against ?? []).length > 0) {
          checkY(10);
          doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.setTextColor(244, 63, 94);
          doc.text('INCONSISTENT EVIDENCE', 18, y); y += 6;
          doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5);
          (top.evidence_against ?? []).forEach(ev => {
            checkY(6);
            doc.setTextColor(244, 63, 94); doc.text('-', 18, y);
            doc.setTextColor(203, 213, 225);
            const lines = doc.splitTextToSize(ev, W - 44);
            doc.text(lines, 23, y);
            y += lines.length * 5 + 1;
          });
        }

        y += 2;
        // Rank explanation
        checkY(14);
        doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.setTextColor(168, 85, 247);
        doc.text('VERIFICATION SHIFT', 18, y); y += 6;
        doc.setFont('helvetica', 'italic'); doc.setFontSize(7.5); doc.setTextColor(148, 163, 184);
        const explLines = doc.splitTextToSize(top.rank_change_explanation ?? '', W - 36);
        doc.text(explLines, 18, y);
        y += explLines.length * 5 + 4;
      }

      // ── PHYSICS METRICS ───────────────────────────────────────────────────
      const physicsResult = physics?.results?.find(r => r.mmsi === top?.mmsi);
      if (physicsResult) {
        sectionHeader('06  PHYSICS VERIFICATION METRICS');
        field('Vessel', physicsResult.vessel_name ?? 'N/A');
        field('Physics Consistency', `${physicsResult.physics_consistency_score}/100`);
        field('Classification', physicsResult.classification ?? 'N/A');
        field('Spatial Overlap', `${physicsResult.metrics?.spatial_overlap_pct?.toFixed(1)}%`);
        field('Centroid Error', `${physicsResult.metrics?.centroid_error_km?.toFixed(2)} km`);
        field('Timing Error', `${physicsResult.metrics?.timing_error_hours?.toFixed(1)} hours`);
        field('Shape Similarity', `${physicsResult.metrics?.shape_similarity_score?.toFixed(2)}`);
      }

      // ── FOOTER on all pages ───────────────────────────────────────────────
      const pageCount = doc.getNumberOfPages();
      for (let p = 1; p <= pageCount; p++) {
        doc.setPage(p);
        doc.setFillColor(6, 11, 20);
        doc.rect(0, 287, W, 10, 'F');
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(6.5);
        doc.setTextColor(71, 85, 105); // slate-600
        doc.text('SlickTrace v2 — Confidential Maritime Forensic Report', 14, 293);
        doc.text(`Page ${p} of ${pageCount}`, W - 14, 293, { align: 'right' });
      }

      // ── Save ──────────────────────────────────────────────────────────────
      doc.save(`slicktrace-dossier-${report.incident_id ?? 'report'}.pdf`);

    } catch (err) {
      console.error('Export failed:', err);
      setExportError('PDF export failed. Check backend connection.');
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
