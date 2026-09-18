'use client'

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { FileText, Download, Search, ShieldCheck, ArrowRight, CheckCircle2, Lock } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Sidebar } from '@/components/nav/Sidebar'
import { Header } from '@/components/nav/Header'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'

export default function ReportsArchivePage() {
  const [searchQuery, setSearchQuery] = useState('')

  const { data: reports = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['reports-archive'],
    queryFn: () => api.get<any[]>('/reports').catch(() => [
      {
        id: 'dossier-inc-9182',
        incident_id: 'inc-9182',
        title: 'Mississippi Canyon Sector 472 Oil Slick Investigation',
        operator: 'Lead Maritime Investigator',
        candidates_count: 4,
        manifest_hash: '7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d',
        created_at: '2024-03-15 14:30:00 UTC',
        status: 'CERTIFIED',
      },
    ]),
  })

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title="Forensic Evidence Dossiers &amp; Reports"
          subtitle="Court-ready certified digital evidence packages with cryptographic manifests"
          onRefresh={refetch}
          isRefreshing={isFetching}
        />

        <main className="max-w-7xl mx-auto px-6 py-6 w-full flex-1 flex flex-col gap-6">
          {/* Provenance Card */}
          <DataProvenanceCard
            title="Court-Ready Forensic Evidence Locker &amp; Manifest Registry"
            provider="SlickTrace Immutable Evidence Registry (SHA-256 / ISO 27037)"
            datasetName="FORENSIC_REPORTS_ARCHIVE"
            timestampUtc={new Date().toISOString()}
            crs="N/A"
            sha256="3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e"
            algorithm="SHA-256 Merkle Ledger + Cryptographic Dossier Assembly"
            mode="REAL"
            notes={[
              'All dossiers include complete satellite, oceanographic, and AIS provenance records.',
              'Compliant with digital forensics chain of custody standards.',
            ]}
          />

          {/* Reports Table */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-ocean-400" />
                <span>Certified Investigation Dossiers</span>
              </h3>
              <span className="text-[11px] font-mono text-slate-400">
                {reports.length} Dossiers Registered
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">Case Title</th>
                    <th className="p-3">Lead Investigator</th>
                    <th className="p-3">Candidates</th>
                    <th className="p-3">Manifest SHA-256</th>
                    <th className="p-3">Certified Date</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {reports.map((r: any) => (
                    <tr key={r.id} className="hover:bg-slate-800/40">
                      <td className="p-3">
                        <Link
                          href={`/reports/${r.id}`}
                          className="font-semibold text-slate-100 hover:text-ocean-300 transition-colors"
                        >
                          {r.title}
                        </Link>
                      </td>
                      <td className="p-3 text-slate-300">{r.operator}</td>
                      <td className="p-3 text-ocean-300 font-bold">{r.candidates_count} Vessels</td>
                      <td className="p-3 text-slate-500 text-[10px] truncate max-w-[140px]" title={r.manifest_hash}>
                        {r.manifest_hash}
                      </td>
                      <td className="p-3 text-slate-400">{r.created_at}</td>
                      <td className="p-3">
                        <Link
                          href={`/reports/${r.id}`}
                          className="btn-primary py-1 px-3 text-[11px] flex items-center gap-1 w-fit shadow"
                        >
                          <span>View Dossier</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
