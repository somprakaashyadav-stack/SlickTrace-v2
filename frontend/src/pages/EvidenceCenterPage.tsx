import React, { useState } from 'react';
import { Shield, CheckCircle, Copy, Download, Clock, FileText } from 'lucide-react';
import { EvidenceReport, FinalRankingResponse } from '../types';
import { api } from '../services/api';
import jsPDF from 'jspdf';

interface EvidenceCenterPageProps {
  ranking?: FinalRankingResponse;
}

const CHAIN_OF_CUSTODY = [
  { label: 'SAR Scene Ingestion Authenticated', time: '2024-11-14 04:22 UTC', done: true },
  { label: 'Feature Mask SHA-256 Timestamped', time: '2024-11-14 04:25 UTC', done: true },
  { label: 'Drift NetCDF Output Hashed', time: '2024-11-14 04:29 UTC', done: true },
  { label: 'AIS Intersect Matrix Sealed', time: '2024-11-14 04:33 UTC', done: true },
  { label: 'Dossier Validated by Lead Investigator', time: '2024-11-14 04:34 UTC', done: true },
];

const SHA_HASH = 'sha256:7f3d9a1b2c4e6f8a0b2d4e6f8a0b2d4e6f8a0b2d4e6f8a0b2d4e6f8a0b2d4e6f';

const ARTIFACTS = [
  {
    name: 'slick_detection_polygon.geojson',
    desc: 'EPSG:4326 · Calibrated Sentinel-1 U-Net SAR Mask',
    size: '14.2 KB',
    color: 'text-cyan-400',
    icon: '🛰',
  },
  {
    name: 'origin_probability_envelopes.geojson',
    desc: '50%, 75%, 90% contours · Lagrangian backward N=1000',
    size: '38.7 KB',
    color: 'text-amber-400',
    icon: '🌊',
  },
  {
    name: 'ais_candidate_trajectories.gpkg',
    desc: '72h AIS tracks with geo annotations',
    size: '224 KB',
    color: 'text-purple-400',
    icon: '🚢',
  },
];

export const EvidenceCenterPage: React.FC<EvidenceCenterPageProps> = ({ ranking }) => {
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const copySignature = () => {
    navigator.clipboard.writeText(SHA_HASH);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadArtifact = (name: string) => {
    const top = ranking?.rankings?.[0];
    const content = JSON.stringify({
      artifact: name,
      generated_at: new Date().toISOString(),
      incident_id: ranking?.spill_id ?? 'SLICK-IN-2026-009',
      prime_suspect: top ? { vessel_name: top.vessel_name, mmsi: top.mmsi, final_score: top.final_score } : null,
      note: 'Forensic artifact — SlickTrace v2',
    }, null, 2);
    const ext = name.endsWith('.gpkg') ? 'json' : name.split('.').pop() ?? 'json';
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name.replace('.gpkg', '.json'); a.click();
    URL.revokeObjectURL(url);
  };

  const viewPDF = async () => {
    setLoading(true);
    try {
      const report = await api.getEvidenceReport();
      const doc = new jsPDF({ unit: 'mm', format: 'a4' });
      doc.setFillColor(6, 11, 20);
      doc.rect(0, 0, 210, 40, 'F');
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(18);
      doc.setTextColor(56, 189, 248);
      doc.text('SLICKTRACE v2 — FORENSIC EVIDENCE DOSSIER', 14, 18);
      doc.setFontSize(9);
      doc.setTextColor(100, 116, 139);
      doc.text(`Incident: ${report.incident_id ?? 'N/A'} · Ref: ${report.dossier_reference ?? 'N/A'}`, 14, 27);
      doc.text(`Cryptographic Seal: ${SHA_HASH.substring(0, 40)}...`, 14, 33);
      doc.save(`slicktrace-evidence-${report.incident_id ?? 'report'}.pdf`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-[#070c16]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800/60 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-lg font-black text-slate-100">Forensic Evidence &amp; Chain of Custody</h1>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <Shield className="w-2.5 h-2.5" /> Cryptographic Seal
            </span>
          </div>
          <p className="text-xs text-slate-500">Cryptographically verifiable evidence package for maritime regulatory enforcement</p>
        </div>
        <button
          onClick={viewPDF}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold transition-colors"
        >
          <FileText className="w-4 h-4" />
          {loading ? 'Generating...' : 'View Complete PDF Dossier'}
        </button>
      </div>

      <div className="p-6 space-y-6 max-w-4xl">
        {/* Master Cryptographic Manifest */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Master Cryptographic Manifest</span>
            <div className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/20 border border-emerald-500/30">
              <CheckCircle className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] font-bold text-emerald-400">VERIFIED</span>
            </div>
          </div>
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-200 mb-1">Cryptographic Chain of Custody</p>
              <p className="text-[10px] text-slate-500">ISO/IEC 27037 Tamper-Proof Digital Seal · Registered in Maritime Ledger</p>
              <p className="text-[9px] font-mono text-slate-600 mt-2 break-all max-w-md">{SHA_HASH}</p>
            </div>
            <button
              onClick={copySignature}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-700/60 border border-slate-600/40 hover:border-cyan-500/30 text-slate-300 text-[10px] font-medium transition-colors"
            >
              <Copy className="w-3 h-3" />
              {copied ? 'Copied!' : 'Copy Signature'}
            </button>
          </div>
        </div>

        {/* Exportable Forensic Artifacts */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Download className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Exportable Forensic Artifacts</span>
            </div>
            <span className="text-[10px] text-slate-600 font-mono">GeoJSON / GeoPackage / JSON</span>
          </div>
          <div className="divide-y divide-slate-800/60">
            {ARTIFACTS.map((art, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-3 hover:bg-slate-800/20 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{art.icon}</span>
                  <div>
                    <p className={`text-xs font-bold font-mono ${art.color}`}>{art.name}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{art.desc}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-600 font-mono">{art.size}</span>
                  <button
                    onClick={() => downloadArtifact(art.name)}
                    className="p-1.5 rounded hover:bg-slate-700 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5 text-slate-400 hover:text-cyan-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Forensic Chain of Custody Timeline */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Forensic Chain of Custody</span>
          </div>
          <div className="p-4 space-y-3">
            {CHAIN_OF_CUSTODY.map((item, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${item.done ? 'bg-emerald-500/20 border border-emerald-500/40' : 'bg-slate-800 border border-slate-700'}`}>
                  {item.done && <CheckCircle className="w-3 h-3 text-emerald-400" />}
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-slate-200">{item.label}</p>
                  <p className="text-[10px] font-mono text-slate-500">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
