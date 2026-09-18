'use client'

import React from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { ArrowLeft, RefreshCw, Waves, ShieldCheck, User } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Incident } from '@/lib/api/types'
import { Sidebar } from '@/components/nav/Sidebar'
import { InvestigationStepper } from '@/components/nav/InvestigationStepper'

export default function IncidentInvestigationLayout({ children }: { children: React.ReactNode }) {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const { data: incident, refetch, isFetching, isLoading } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => api.get<Incident>(`/incidents/${id}`),
    enabled: !!id,
  })

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-20">
          <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link
                href="/incidents"
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/80"
                title="Back to Investigations Directory"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="font-bold text-base text-slate-100">
                    {incident?.title || (isLoading ? 'Loading Case...' : 'Investigation Case')}
                  </h1>
                  <span className="text-xs text-slate-500 font-mono">ID: {id?.slice(0, 8)}</span>
                  {incident?.mode === 'demo' ? (
                    <span className="badge-demo">DEMO</span>
                  ) : (
                    <span className="badge-real">REAL MODE</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400">
                  Lead: <strong className="text-slate-300">{incident?.operator || 'Analyst'}</strong> · Status:{' '}
                  <span className="uppercase font-semibold text-ocean-300">
                    {incident?.status?.replace('_', ' ') || 'OPEN'}
                  </span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
                <span>{isFetching ? 'Syncing...' : 'Sync Pipeline'}</span>
              </button>
            </div>
          </div>
        </header>

        {/* 01-08 Stage Stepper Navigation */}
        <div className="max-w-7xl mx-auto px-6 pt-4 w-full">
          <InvestigationStepper incidentId={id} currentStatus={incident?.status} />
        </div>

        {/* Stage Content */}
        <main className="max-w-7xl mx-auto px-6 py-5 w-full flex-1 flex flex-col">
          {children}
        </main>
      </div>
    </div>
  )
}
