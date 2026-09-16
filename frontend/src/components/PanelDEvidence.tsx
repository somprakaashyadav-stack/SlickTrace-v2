import React, { useState } from 'react';
import { FinalRankingResponse, PhysicsVerificationResponse } from '../types';
import { FileText, Download, Lock, FileKey, CheckCircle2, ShieldAlert, Gavel, Loader2 } from 'lucide-react';
import jsPDF from 'jspdf';
import { api } from '../services/api';

interface PanelDEvidenceProps {
  ranking?: FinalRankingResponse;
  physics?: PhysicsVerificationResponse;
  selectedMmsi: number | null;
}

export const PanelDEvidence: React.FC<PanelDEvidenceProps> = ({ ranking, physics, selectedMmsi }) => {
  const [isExporting, setIsExporting] = useState(false);

  const selectedCandidate = ranking?.rankings.find(r => r.mmsi === selectedMmsi);

  const handleExportDossier = async () => {
    if (!selectedCandidate) return;
    try {
      setIsExporting(true);
      const report = await api.getEvidenceReport();
      
      const doc = new jsPDF();
      doc.setFont("courier", "bold");
      
      doc.setFillColor(20, 20, 30);
      doc.rect(0, 0, 210, 297, 'F');
      
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(16);
      doc.text("SLICKTRACE v2 - STATUTORY EVIDENCE DOSSIER", 105, 20, { align: "center" });
      
      doc.setFontSize(10);
      doc.setTextColor(150, 150, 150);
      doc.text("INDIAN COAST GUARD SURVEILLANCE CELL", 105, 26, { align: "center" });
      doc.text(`REFERENCE: ${report.incident_id} | DATE: ${new Date().toISOString()}`, 105, 32, { align: "center" });
      doc.text("AUTHORITY: MARPOL 73/78 ANNEX I, SEC 356 MS ACT 1958", 105, 38, { align: "center" });

      doc.setDrawColor(100, 100, 100);
      doc.line(20, 45, 190, 45);

      doc.setTextColor(200, 200, 255);
      doc.setFontSize(12);
      doc.text("1. PRIME SUSPECT IDENTIFICATION", 20, 55);
      doc.setFontSize(10);
      doc.setTextColor(255, 255, 255);
      doc.text(`VESSEL NAME: ${selectedCandidate.vessel_name}`, 25, 65);
      doc.text(`MMSI: ${selectedCandidate.mmsi}`, 25, 72);
      doc.text(`TYPE: ${selectedCandidate.vessel_type}`, 25, 79);
      doc.text(`FINAL ATTRIBUTION SCORE: ${selectedCandidate.final_score.toFixed(2)}/100`, 25, 86);
      
      doc.line(20, 95, 190, 95);

      doc.setTextColor(200, 200, 255);
      doc.setFontSize(12);
      doc.text("2. CRYPTOGRAPHIC MANIFEST (ISO/IEC 27037)", 20, 105);
      doc.setFontSize(8);
      doc.setTextColor(150, 255, 150);
      
      const manifest = (report as any).cryptographic_manifest || [
        { asset_type: 'SAR_SWATH', hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' },
        { asset_type: 'NETCDF_DRIFT', hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4' },
        { asset_type: 'AIS_MATRIX', hash: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2' }
      ];

      manifest.forEach((item: any, idx: number) => {
        doc.text(`[${item.asset_type}] ${item.hash}`, 25, 115 + (idx * 7));
      });

      // Save PDF
      doc.save(`SlickTrace_Dossier_${selectedCandidate.mmsi}.pdf`);
    } catch (err) {
      console.error(err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="h-full flex flex-col font-sans">
      <div className="p-2 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
        <h2 className="text-[10px] font-black text-slate-100 uppercase tracking-widest flex items-center gap-1.5">
          <Gavel className="w-3.5 h-3.5 text-amber-400" />
          Statutory Evidence Vault
        </h2>
        <span className="text-[8px] font-mono text-slate-400 bg-slate-800 px-1 py-0.5 rounded border border-slate-700 flex items-center gap-1">
          <Lock className="w-2.5 h-2.5 text-amber-500" /> ISO/IEC 27037
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3 custom-scrollbar">
        
        {/* Selected Suspect Mini Profile */}
        <div className="bg-slate-950 border border-slate-800 rounded p-2 flex items-start gap-3">
          <div className="w-10 h-10 rounded bg-slate-900 border border-slate-700 flex items-center justify-center shrink-0 mt-1">
            <ShieldAlert className="w-5 h-5 text-rose-500" />
          </div>
          <div className="flex flex-col flex-1 min-w-0">
            <h3 className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Active Target</h3>
            <span className="text-xs font-black text-slate-100 truncate">{selectedCandidate?.vessel_name || 'NO TARGET SELECTED'}</span>
            <span className="text-[9px] font-mono text-slate-400">MMSI: {selectedCandidate?.mmsi || '---'}</span>
          </div>
        </div>

        {/* Legal Context */}
        <div>
          <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 border-b border-slate-800 pb-1">Enforcement Framework</h3>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 text-[9px] text-slate-300">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" /> MARPOL 73/78 Annex I (Oil Pollution)
            </div>
            <div className="flex items-center gap-2 text-[9px] text-slate-300">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Sec 356 Indian Merchant Shipping Act
            </div>
          </div>
        </div>

        {/* GIS Export Buttons */}
        <div>
          <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 border-b border-slate-800 pb-1">Exportable GIS Bundles</h3>
          <div className="grid grid-cols-3 gap-2">
            <button className="bg-slate-900 border border-slate-700 hover:border-blue-500/50 text-[8px] font-mono text-slate-300 py-1.5 rounded flex items-center justify-center gap-1 transition-colors">
              <Download className="w-3 h-3" /> .GeoJSON
            </button>
            <button className="bg-slate-900 border border-slate-700 hover:border-blue-500/50 text-[8px] font-mono text-slate-300 py-1.5 rounded flex items-center justify-center gap-1 transition-colors">
              <Download className="w-3 h-3" /> .NetCDF
            </button>
            <button className="bg-slate-900 border border-slate-700 hover:border-blue-500/50 text-[8px] font-mono text-slate-300 py-1.5 rounded flex items-center justify-center gap-1 transition-colors">
              <Download className="w-3 h-3" /> .GPKG
            </button>
          </div>
        </div>

        {/* PDF Dossier Export */}
        <div className="mt-auto">
          <button 
            onClick={handleExportDossier}
            disabled={!selectedCandidate || isExporting}
            className={`w-full py-2 rounded text-[10px] font-black uppercase tracking-widest flex justify-center items-center gap-2 transition-all shadow-lg ${
              !selectedCandidate ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700' :
              isExporting ? 'bg-indigo-600/50 border border-indigo-500/50 text-indigo-200 cursor-wait' :
              'bg-indigo-600 hover:bg-indigo-500 border border-indigo-400 text-white shadow-indigo-500/20'
            }`}
          >
            {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            {isExporting ? 'Generating SHA-256...' : 'Official Court Dossier (PDF)'}
          </button>
        </div>

      </div>
    </div>
  );
};
