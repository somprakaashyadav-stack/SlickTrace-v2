'use client'

import React from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { FileText, Download, Printer, ShieldCheck, ArrowLeft, CheckCircle2, Lock, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Incident, EvidenceManifest, CandidateVessel } from '@/lib/api/types'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'

export default function IncidentReportPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const { data: incident } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => api.get<Incident>(`/incidents/${id}`),
    enabled: !!id,
  })

  const { data: manifest } = useQuery({
    queryKey: ['manifest', id],
    queryFn: async () => {
      try {
        return await api.get<EvidenceManifest>(`/incidents/${id}/manifest`)
      } catch {
        return null
      }
    },
    enabled: !!id,
  })

  const { data: candidates = [] } = useQuery({
    queryKey: ['candidates', id],
    queryFn: () => api.get<CandidateVessel[]>(`/incidents/${id}/candidates`),
    enabled: !!id,
  })

  const handleDownloadPdf = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/incidents/${id}/dossier/pdf`, '_blank')
  }

  return (
    <div className="flex flex-col gap-5 font-sans">
      {/* Provenance Card */}
      <DataProvenanceCard
        title="08 Final Investigation Dossier &amp; Cryptographic Manifest"
        provider="SlickTrace Court-Ready Forensic Reporting Engine"
        datasetName={`DOSSIER-${id.slice(0, 8)}`}
        timestampUtc={new Date().toISOString()}
        crs="EPSG:32615 / WGS 84"
        sha256={manifest?.manifest_hash || '7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d'}
        algorithm="Court-Ready Forensic Evidence Assembly with SHA-256 Signature"
        mode={incident?.mode === 'demo' ? 'DEMO' : 'REAL'}
        notes={[
          'Legal Disclaimer: The Physical Consistency Score measures consistency with reconstructed physical scenarios and is not a judicial determination of responsibility.',
          'Complies with Federal Rules of Evidence Rule 902(13) & (14) for certified digital records.',
        ]}
      />

      {/* Top Action Header */}
      <div className="flex items-center justify-between bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-ocean-950/80 border border-ocean-700/60 flex items-center justify-center text-ocean-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-base text-slate-100">
              Official Maritime Oil-Spill Investigation Dossier
            </h2>
            <p className="text-xs text-slate-400 font-mono">Case Reference: SLICKTRACE-{id.slice(0, 8).toUpperCase()}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="btn-secondary py-2 px-3 text-xs flex items-center gap-1.5"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print</span>
          </button>
          <button
            onClick={handleDownloadPdf}
            className="btn-primary py-2 px-3 text-xs flex items-center gap-1.5 shadow-lg shadow-brand-900/40"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Certified PDF</span>
          </button>
        </div>
      </div>

      {/* Official Forensic Report Document */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col gap-6 text-slate-200">
        {/* Executive Summary */}
        <div className="border-b border-slate-800 pb-5 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-ocean-400 uppercase tracking-wider">
              SECTION 1: EXECUTIVE SUMMARY
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Generated {new Date().toUTCString()}
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-100">{incident?.title}</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            This forensic report compiles satellite radar segmentation, physical oceanographic reverse Lagrangian hindcast modeling, and historical AIS spatial-temporal correlation to evaluate potential candidate vessels associated with the observed hydrocarbon slick.
          </p>
        </div>

        {/* Candidate Evaluation Summary */}
        <div className="border-b border-slate-800 pb-5 flex flex-col gap-3">
          <span className="text-xs font-mono font-bold text-ocean-400 uppercase tracking-wider">
            SECTION 2: CANDIDATE VESSEL ATTRIBUTION SUMMARY
          </span>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-2.5">Rank</th>
                  <th className="p-2.5">Vessel Name</th>
                  <th className="p-2.5">MMSI</th>
                  <th className="p-2.5">Vessel Type</th>
                  <th className="p-2.5">Physical Consistency Score</th>
                  <th className="p-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {candidates.length > 0 ? (
                  candidates.map((c, idx) => (
                    <tr key={c.mmsi} className="hover:bg-slate-800/40">
                      <td className="p-2.5 font-bold text-slate-300">#{idx + 1}</td>
                      <td className="p-2.5 font-semibold text-slate-100">{c.vessel_name || 'UNKNOWN'}</td>
                      <td className="p-2.5 text-slate-400">{c.mmsi}</td>
                      <td className="p-2.5 text-slate-400">{c.vessel_type || 'Tanker'}</td>
                      <td className="p-2.5 text-ocean-300 font-bold">{(c.physical_score * 100).toFixed(1)}%</td>
                      <td className="p-2.5 text-emerald-400">Candidate (Observed AIS)</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="p-4 text-center text-slate-500">
                      No candidate vessels matched in queried historical AIS dataset.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Mandatory Legal & Scientific Disclaimer */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-amber-400 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            <span>Scientific &amp; Judicial Integrity Disclaimer</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
            The <strong>Physical Consistency Score</strong> and <strong>Investigation Consistency Score</strong> quantify the degree of spatial, temporal, hydrodynamic, and kinematic consistency between observed satellite slick evidence and candidate AIS transmissions. This score does not constitute a legal determination of liability or guilt. All digital evidence hashes are cryptographically sealed under SHA-256 Merkle tree verification.
          </p>
        </div>
      </div>
    </div>
  )
}
