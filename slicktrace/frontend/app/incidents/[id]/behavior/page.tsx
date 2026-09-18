'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Activity, ArrowRight, ArrowLeft, ShieldAlert, Sparkles, Sliders, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Incident, CandidateVessel } from '@/lib/api/types'
import { ScoreBreakdown } from '@/components/scoring/ScoreBreakdown'
import { VesselCandidateTable } from '@/components/ais/VesselCandidateTable'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'

export default function IncidentBehaviorPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const { data: incident } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => api.get<Incident>(`/incidents/${id}`),
    enabled: !!id,
  })

  const { data: candidates = [] } = useQuery({
    queryKey: ['candidates', id],
    queryFn: () => api.get<CandidateVessel[]>(`/incidents/${id}/candidates`),
    enabled: !!id,
  })

  const [selectedCandidate, setSelectedCandidate] = useState<CandidateVessel | null>(
    candidates.length > 0 ? candidates[0] : null
  )

  const activeVessel = selectedCandidate || (candidates.length > 0 ? candidates[0] : null)

  return (
    <div className="flex flex-col gap-5 font-sans">
      {/* Provenance Card */}
      <DataProvenanceCard
        title="05 Vessel Trajectory &amp; Kinematic Anomaly Analysis Provenance"
        provider="SlickTrace Explainable Kinematics + Isolation Forest Engine"
        datasetName={activeVessel ? `MMSI-${activeVessel.mmsi}` : 'KINEMATICS-EVAL'}
        timestampUtc={new Date().toISOString()}
        crs="EPSG:4326 (WGS 84 Geodesic Sinuosity / Nautical Knots)"
        sha256="8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e"
        algorithm="Rule-Based Kinematic Feature Extraction + Isolation Forest Anomaly Scoring"
        mode={incident?.mode === 'demo' ? 'DEMO' : 'REAL'}
        notes={[
          'AIS transmission gaps are observation anomalies and are never automatically labeled as intentional shutdown.',
          'Physical Consistency Score reflects physics-based consistency with reconstructed drift scenario, not guilt.',
        ]}
      />

      {/* Main Grid: Candidate Table + Score Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-ocean-400" />
                <span>Candidate Vessel Kinematics &amp; Anomalies</span>
              </h3>
              <span className="text-[11px] font-mono text-slate-400">
                {candidates.length} Candidate(s) Evaluated
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Select a candidate vessel below to inspect its 14 kinematic metrics, speed profile, turn rates, and explainable anomaly breakdown.
            </p>
          </div>

          <VesselCandidateTable
            candidates={candidates}
            onSelectCandidate={(c) => setSelectedCandidate(c)}
          />

          <div className="flex items-center justify-between gap-2 pt-2">
            <Link
              href={`/incidents/${id}/vessels`}
              className="btn-secondary py-2 text-xs flex items-center gap-1.5 flex-1 justify-center"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>04 AIS Candidates</span>
            </Link>
            <Link
              href={`/incidents/${id}/verification`}
              className="btn-primary py-2 text-xs flex items-center gap-1.5 flex-1 justify-center"
            >
              <span>06 Verification</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        <div className="lg:col-span-5 flex flex-col gap-4">
          <ScoreBreakdown candidate={activeVessel} />
        </div>
      </div>
    </div>
  )
}
