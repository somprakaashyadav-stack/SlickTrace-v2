'use client'

import { AlertTriangle, ShieldCheck, Database } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

interface HealthResponse {
  status: string
  mode: 'real' | 'demo'
  version: string
  unavailable_sources: Record<string, string>
}

export function ModeGuard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthResponse>('/health'),
    refetchInterval: 30000,
  })

  const isDemo = health?.mode === 'demo'
  const unavailableSources = health?.unavailable_sources
    ? Object.entries(health.unavailable_sources)
    : []

  return (
    <aside aria-label="System operational mode and status alerts" className="w-full flex flex-col">
      {/* Mode Banner */}
      {isDemo ? (
        <div className="bg-amber-600/90 text-white px-4 py-2 text-xs font-semibold flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-200 animate-bounce" />
            <span>
              DEMO MODE ACTIVE — Using offline fixtures. Real satellite and AIS pipelines are simulated.
            </span>
          </div>
          <span className="bg-amber-900/60 px-2 py-0.5 rounded text-[10pt] uppercase tracking-wider">
            Demonstration Only
          </span>
        </div>
      ) : (
        <div className="bg-slate-900 border-b border-slate-800 text-slate-400 px-4 py-1.5 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">REAL MODE</span>
            <span className="text-slate-500">|</span>
            <span>Real Copernicus, MarineCadastre &amp; OpenDrift integrations active</span>
          </div>
          <span className="text-[10pt] text-emerald-400 flex items-center gap-1 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            LIVE
          </span>
        </div>
      )}

      {/* Unavailable External Data Warning */}
      {unavailableSources.length > 0 && !isDemo && (
        <div className="bg-amber-950/40 border-b border-amber-900/50 px-4 py-1.5 text-xs text-amber-300 flex items-center gap-2 overflow-x-auto">
          <Database className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
          <span className="font-semibold text-amber-200">Notice:</span>
          <span>Unavailable live APIs:</span>
          <div className="flex items-center gap-2">
            {unavailableSources.map(([source]) => (
              <span
                key={source}
                className="bg-amber-900/40 px-1.5 py-0.5 rounded text-[10pt] font-mono text-amber-200 border border-amber-800"
              >
                {source}
              </span>
            ))}
          </div>
          <span className="text-amber-400/80 text-[10pt] ml-auto">
            (Pipelines will surface explicit UNAVAILABLE state rather than fallback)
          </span>
        </div>
      )}
    </aside>
  )
}
