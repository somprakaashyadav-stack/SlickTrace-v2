'use client'

import React, { useState } from 'react'
import { ShieldCheck, ChevronDown, ChevronUp, Database, Clock, Compass, Hash, Cpu, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface DataProvenanceProps {
  title?: string
  provider?: string
  datasetName?: string
  timestampUtc?: string
  crs?: string
  sha256?: string
  algorithm?: string
  modelCheckpoint?: string
  forcingSources?: {
    wind?: string
    currents?: string
    waves?: string
  }
  notes?: string[]
  mode?: 'REAL' | 'DEMO'
  className?: string
}

export function DataProvenanceCard({
  title = 'Data Provenance & Cryptographic Chain of Custody',
  provider,
  datasetName,
  timestampUtc,
  crs,
  sha256,
  algorithm,
  modelCheckpoint,
  forcingSources,
  notes = [],
  mode = 'REAL',
  className,
}: DataProvenanceProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div
      className={cn(
        'bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 shadow-md font-sans text-xs',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-200">{title}</span>
          <span
            className={cn(
              'text-[9px] font-mono px-1.5 py-0.5 rounded font-bold uppercase',
              mode === 'REAL'
                ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700/50'
                : 'bg-amber-950/80 text-amber-300 border border-amber-700/50'
            )}
          >
            {mode} DATA
          </span>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-slate-200 p-1 flex items-center gap-1 text-[11px] font-mono"
        >
          <span>{isExpanded ? 'Hide Details' : 'Verify Provenance'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Summary Line */}
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 font-mono">
        {provider && (
          <div className="flex items-center gap-1">
            <Database className="w-3 h-3 text-ocean-400" />
            <span>Provider: <strong className="text-slate-300">{provider}</strong></span>
          </div>
        )}
        {timestampUtc && (
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3 text-ocean-400" />
            <span>UTC: <strong className="text-slate-300">{timestampUtc}</strong></span>
          </div>
        )}
        {crs && (
          <div className="flex items-center gap-1">
            <Compass className="w-3 h-3 text-ocean-400" />
            <span>CRS: <strong className="text-slate-300">{crs}</strong></span>
          </div>
        )}
      </div>

      {/* Expanded Provenance Table */}
      {isExpanded && (
        <div className="mt-3 bg-slate-950/70 rounded-lg p-3 border border-slate-800 flex flex-col gap-2 font-mono text-[10.5px]">
          {datasetName && (
            <div className="flex justify-between border-b border-slate-800/60 pb-1">
              <span className="text-slate-500">Dataset ID:</span>
              <span className="text-slate-300 font-semibold">{datasetName}</span>
            </div>
          )}

          {algorithm && (
            <div className="flex justify-between border-b border-slate-800/60 pb-1">
              <span className="text-slate-500">Algorithm / Engine:</span>
              <span className="text-sky-300">{algorithm}</span>
            </div>
          )}

          {modelCheckpoint && (
            <div className="flex justify-between border-b border-slate-800/60 pb-1">
              <span className="text-slate-500">Model Weights SHA:</span>
              <span className="text-amber-300 truncate max-w-[280px]" title={modelCheckpoint}>
                {modelCheckpoint}
              </span>
            </div>
          )}

          {forcingSources && (
            <div className="flex flex-col gap-1 border-b border-slate-800/60 pb-1">
              <span className="text-slate-500">Environmental Forcing Inputs:</span>
              <div className="grid grid-cols-3 gap-1 pl-2 text-[10px]">
                <div>Wind: <span className="text-slate-300">{forcingSources.wind || 'ERA5 (ECMWF)'}</span></div>
                <div>Currents: <span className="text-slate-300">{forcingSources.currents || 'CMEMS GLOBAL'}</span></div>
                <div>Waves: <span className="text-slate-300">{forcingSources.waves || 'CMEMS WAM'}</span></div>
              </div>
            </div>
          )}

          {sha256 && (
            <div className="flex justify-between border-b border-slate-800/60 pb-1">
              <span className="text-slate-500 flex items-center gap-1">
                <Hash className="w-3 h-3 text-emerald-400" />
                <span>SHA-256 Digest:</span>
              </span>
              <span className="text-emerald-300 select-all font-mono truncate max-w-[320px]" title={sha256}>
                {sha256}
              </span>
            </div>
          )}

          {notes && notes.length > 0 && (
            <div className="flex flex-col gap-0.5 pt-1">
              <span className="text-slate-500">Forensic Notes:</span>
              {notes.map((note, idx) => (
                <div key={idx} className="text-slate-400 pl-2 text-[10px]">
                  • {note}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
