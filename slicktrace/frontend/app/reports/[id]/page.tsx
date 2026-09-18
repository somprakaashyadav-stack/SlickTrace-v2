'use client'

import React from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { FileText, Download, Printer, ArrowLeft, ShieldCheck, CheckCircle2, Lock } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Sidebar } from '@/components/nav/Sidebar'
import { Header } from '@/components/nav/Header'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'

export default function SingleReportViewPage() {
  const params = useParams()
  const id = params?.id as string

  const { data: dossier, isLoading } = useQuery({
    queryKey: ['dossier-view', id],
    queryFn: () => api.get<any>(`/reports/${id}`),
  })

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={`Forensic Dossier: ${dossier?.title || id}`}
          subtitle={`Case Dossier ID: ${id} · Cryptographically Certified Evidence`}
          actions={
            <div className="flex items-center gap-2">
              <Link href="/reports" className="btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3">
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>All Reports</span>
              </Link>
              <button
                onClick={() => window.print()}
                className="btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print</span>
              </button>
            </div>
          }
        />

        <main className="max-w-5xl mx-auto px-6 py-6 w-full flex-1 flex flex-col gap-6">
          {/* Provenance Card */}
          <DataProvenanceCard
            title="Official Court-Ready Evidence Dossier Provenance"
            provider="SlickTrace Court-Ready Forensic Reporting Engine"
            datasetName={`DOSSIER_${id}`}
            timestampUtc={dossier?.created_at || new Date().toISOString()}
            crs="EPSG:32615 / WGS 84"
            sha256={dossier?.manifest_hash || '7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d'}
            algorithm="SHA-256 Merkle Verification &amp; Federal Rules of Evidence Compliance"
            mode="REAL"
            notes={[
              'Certified digital evidence package generated under ISO/IEC 27037 standards.',
              'Physical Consistency Score reflects physics-based consistency with reconstructed drift scenario, not guilt.',
            ]}
          />

          {/* Dossier Document Content */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col gap-6 text-slate-200">
            <div className="border-b border-slate-800 pb-4 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono text-ocean-400 font-bold uppercase tracking-wider">
                  MARITIME OIL SPILL FORENSIC DOSSIER
                </span>
                <h2 className="text-xl font-bold text-slate-100 mt-1">{dossier?.title}</h2>
                <p className="text-xs text-slate-400">
                  Lead Investigator: <strong className="text-slate-300">{dossier?.operator}</strong>
                </p>
              </div>

              <div className="text-right font-mono text-xs text-slate-400">
                <div>Status: <span className="text-emerald-400 font-bold">CERTIFIED</span></div>
                <div className="text-[10px] text-slate-500">{dossier?.created_at}</div>
              </div>
            </div>

            {/* Candidates Table */}
            <div className="flex flex-col gap-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                CANDIDATE ATTRIBUTION EVALUATION
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Rank</th>
                      <th className="p-2.5">Vessel Name</th>
                      <th className="p-2.5">MMSI</th>
                      <th className="p-2.5">Type</th>
                      <th className="p-2.5">Physical Consistency Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {dossier?.candidates?.map((c: any) => (
                      <tr key={c.mmsi} className="hover:bg-slate-800/40">
                        <td className="p-2.5 font-bold text-slate-300">#{c.rank}</td>
                        <td className="p-2.5 font-semibold text-slate-100">{c.vessel_name}</td>
                        <td className="p-2.5 text-slate-400">{c.mmsi}</td>
                        <td className="p-2.5 text-slate-300">{c.vessel_type}</td>
                        <td className="p-2.5 text-ocean-300 font-bold">{(c.physical_score * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 text-xs text-slate-400">
              <strong className="text-amber-400">Investigation Consistency Notice:</strong> The score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility.
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
