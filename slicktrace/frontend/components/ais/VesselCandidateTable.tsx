'use client'

import React, { useState } from 'react'
import { CandidateVessel } from '@/lib/api/types'
import { ShieldAlert, AlertTriangle, CheckCircle2, ChevronRight, Check, X, Compass, Anchor } from 'lucide-react'
import { cn } from '@/lib/utils'

interface VesselCandidateTableProps {
  candidates: CandidateVessel[]
  onSelectCandidate?: (candidate: CandidateVessel) => void
  onVerifyCounterfactual?: (candidateId: string) => void
}

export function VesselCandidateTable({
  candidates,
  onSelectCandidate,
  onVerifyCounterfactual,
}: VesselCandidateTableProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  if (!candidates || candidates.length === 0) {
    return (
      <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-8 text-center text-slate-400">
        <Anchor className="w-10 h-10 mx-auto text-slate-600 mb-2" />
        <p className="font-medium text-slate-300">No Candidate Vessels Found</p>
        <p className="text-xs mt-1">Execute the AIS Spatiotemporal search against the hindcast origin window.</p>
      </div>
    )
  }

  return (
    <div className="bg-slate-800/90 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
            <span>Identified Suspect Vessels</span>
            <span className="bg-brand-900/60 text-brand-300 text-xs px-2 py-0.5 rounded-full border border-brand-800">
              {candidates.length} candidate{candidates.length === 1 ? '' : 's'}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Ranked by multi-factor physical consistency and behavioral anomaly score
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-850 text-slate-400 uppercase tracking-wider font-semibold">
              <th className="py-2.5 px-3 w-12 text-center">Rank</th>
              <th className="py-2.5 px-3">Vessel &amp; MMSI</th>
              <th className="py-2.5 px-3">Type &amp; Flag</th>
              <th className="py-2.5 px-3">Approach Dist</th>
              <th className="py-2.5 px-3">Physical Score</th>
              <th className="py-2.5 px-3">Observed Anomalies</th>
              <th className="py-2.5 px-3 text-center">Counterfactual</th>
              <th className="py-2.5 px-3 w-10"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/60">
            {candidates.map((v) => {
              const isSelected = selectedId === v.id
              const isHighGuilt = (v.physical_score ?? 0) >= 65
              const isMedGuilt = (v.physical_score ?? 0) >= 40 && (v.physical_score ?? 0) < 65

              return (
                <tr
                  key={v.id}
                  onClick={() => {
                    setSelectedId(v.id)
                    if (onSelectCandidate) onSelectCandidate(v)
                  }}
                  className={cn(
                    'cursor-pointer transition-colors',
                    isSelected ? 'bg-brand-950/40 border-l-2 border-brand-500' : 'hover:bg-slate-750'
                  )}
                >
                  <td className="py-3 px-3 text-center font-bold">
                    <span
                      className={cn(
                        'inline-block w-6 h-6 rounded-full text-center leading-6 text-xs',
                        v.rank === 1
                          ? 'bg-rose-500 text-white shadow-sm'
                          : v.rank === 2
                          ? 'bg-amber-500 text-white shadow-sm'
                          : 'bg-slate-700 text-slate-300'
                      )}
                    >
                      #{v.rank ?? '-'}
                    </span>
                  </td>

                  <td className="py-3 px-3">
                    <div className="font-semibold text-slate-200">{v.vessel_name || 'UNIDENTIFIED'}</div>
                    <div className="font-mono text-slate-400 text-[10pt]">MMSI: {v.mmsi}</div>
                  </td>

                  <td className="py-3 px-3">
                    <div className="text-slate-300">{v.vessel_type || 'Unknown'}</div>
                    <div className="text-slate-500 text-[10pt]">{v.flag_state || 'N/A'}</div>
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-300">
                    {v.closest_approach_km ? `${v.closest_approach_km.toFixed(1)} km` : 'N/A'}
                  </td>

                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full',
                            isHighGuilt ? 'bg-rose-500' : isMedGuilt ? 'bg-amber-500' : 'bg-ocean-500'
                          )}
                          style={{ width: `${Math.min(v.physical_score ?? 0, 100)}%` }}
                        />
                      </div>
                      <span
                        className={cn(
                          'font-bold font-mono',
                          isHighGuilt ? 'text-rose-400' : isMedGuilt ? 'text-amber-400' : 'text-ocean-300'
                        )}
                      >
                        {v.physical_score?.toFixed(1) ?? '0.0'}
                      </span>
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    {v.anomalies && v.anomalies.length > 0 ? (
                      <div className="flex flex-col gap-1">
                        {v.anomalies.slice(0, 2).map((a, i) => (
                          <span
                            key={i}
                            className="bg-rose-950/60 border border-rose-900/80 text-rose-300 px-1.5 py-0.5 rounded text-[9pt] flex items-center gap-1 w-fit"
                          >
                            <AlertTriangle className="w-2.5 h-2.5 flex-shrink-0" />
                            {a}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-500 text-[10pt] italic">Normal behavior</span>
                    )}
                  </td>

                  <td className="py-3 px-3 text-center">
                    {v.counterfactual_run ? (
                      v.counterfactual_consistent ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-[10pt]">
                          <Check className="w-3 h-3" /> Consistent
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-400 font-semibold text-[10pt]">
                          <X className="w-3 h-3" /> Inconsistent
                        </span>
                      )
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          if (onVerifyCounterfactual) onVerifyCounterfactual(v.id)
                        }}
                        className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-2 py-1 rounded text-[10pt] transition-colors"
                      >
                        Run Forward
                      </button>
                    )}
                  </td>

                  <td className="py-3 px-3 text-right">
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
