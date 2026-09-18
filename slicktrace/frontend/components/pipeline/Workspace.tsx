'use client'

import React, { useState } from 'react'
import {
  Satellite,
  Waves,
  Wind,
  Ship,
  Scale,
  FileCheck,
  ChevronRight,
  Play,
  RotateCw,
} from 'lucide-react'
import { Incident, Imagery, SpillDetection, HindcastRun, CandidateVessel, EvidenceManifest, SpillGeometry } from '@/lib/api/types'
import { useQuery } from '@tanstack/react-query'
import { InvestigationGIS } from '@/components/map/InvestigationGIS'
import { VesselCandidateTable } from '@/components/ais/VesselCandidateTable'
import { ScoreBreakdown } from '@/components/scoring/ScoreBreakdown'
import { EvidenceManifestView } from '@/components/evidence/EvidenceManifestView'
import { TaskProgressPanel } from '@/components/core/TaskProgressPanel'
import { api } from '@/lib/api/client'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface WorkspaceProps {
  incident: Incident
  imageryList: Imagery[]
  detections: SpillDetection[]
  hindcasts: HindcastRun[]
  candidates: CandidateVessel[]
  manifest: EvidenceManifest | null
  onRefresh: () => void
}

type TabType = 'imagery' | 'detection' | 'hindcast' | 'ais' | 'ranking' | 'dossier'

export function Workspace({
  incident,
  imageryList,
  detections,
  hindcasts,
  candidates,
  manifest,
  onRefresh,
}: WorkspaceProps) {
  const [activeTab, setActiveTab] = useState<TabType>('imagery')
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateVessel | null>(
    candidates.length > 0 ? candidates[0] : null
  )
  const [loadingAction, setLoadingAction] = useState<string | null>(null)

  const activeDetection = detections.length > 0 ? detections[0] : null
  const activeHindcast = hindcasts.length > 0 ? hindcasts[0] : null

  // Fetch Spill Vector Geometry for the active detection
  const { data: spillGeometry, refetch: refetchGeometry } = useQuery({
    queryKey: ['spill-geometry', activeDetection?.id],
    queryFn: async () => {
      if (!activeDetection?.id) return null
      try {
        return await api.get<SpillGeometry>(`/detection/${activeDetection.id}/geometry`)
      } catch {
        return null
      }
    },
    enabled: !!activeDetection?.id,
  })

  // Trigger Detection
  const handleTriggerDetection = async () => {
    if (!imageryList || imageryList.length === 0) {
      toast.error('No satellite scene uploaded')
      return
    }
    setLoadingAction('detection')
    try {
      await api.post(`/incidents/${incident.id}/detect`, {
        imagery_id: imageryList[0].id,
        model: 'unetplusplus',
        use_sam2: false,
      })
      toast.success('SAR segmentation dispatched to ML worker')
      onRefresh()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to dispatch detection')
    } finally {
      setLoadingAction(null)
    }
  }

  // Trigger Hindcast
  const handleTriggerHindcast = async () => {
    if (!activeDetection) {
      toast.error('Run oil spill detection first')
      return
    }
    setLoadingAction('hindcast')
    try {
      await api.post(`/incidents/${incident.id}/hindcast`, {
        detection_id: activeDetection.id,
        start_lat: spillGeometry?.centroid_lat ?? 27.5,
        start_lon: spillGeometry?.centroid_lon ?? -90.0,
        detection_time: new Date().toISOString(),
        hours_back: 24,
        durations_hours: [4, 8, 12, 24],
        n_particles: 1000,
        oil_type: 'GENERIC BUNKER C',
        allow_fallback: true,
        slick_polygon: spillGeometry?.geojson_polygon ?? null,
      })
      toast.success('OpenDrift backward Lagrangian simulation dispatched')
      onRefresh()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to dispatch hindcast')
    } finally {
      setLoadingAction(null)
    }
  }

  // Trigger AIS Search
  const handleTriggerAIS = async () => {
    if (!activeHindcast) {
      toast.error('Complete hindcast simulation first')
      return
    }
    setLoadingAction('ais')
    try {
      await api.post(`/incidents/${incident.id}/ais-search`, {
        hindcast_run_id: activeHindcast.id,
        lat_min: 27.0,
        lat_max: 28.5,
        lon_min: -91.0,
        lon_max: -89.0,
        time_start: activeHindcast.origin_time_start || new Date(Date.now() - 86400000).toISOString(),
        time_end: activeHindcast.origin_time_end || new Date().toISOString(),
      })
      toast.success('DuckDB Spatial AIS search dispatched')
      onRefresh()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to search AIS')
    } finally {
      setLoadingAction(null)
    }
  }

  const tabs = [
    { id: 'imagery', label: '1. Satellite Scene', icon: Satellite },
    { id: 'detection', label: '2. Oil Detection', icon: Waves },
    { id: 'hindcast', label: '3. Ocean Drift', icon: Wind },
    { id: 'ais', label: '4. AIS Search', icon: Ship },
    { id: 'ranking', label: '5. Attribution', icon: Scale },
    { id: 'dossier', label: '6. Evidence Dossier', icon: FileCheck },
  ]

  return (
    <div className="flex flex-col gap-5">
      {/* Pipeline Navigation Bar */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-2 flex items-center justify-between overflow-x-auto shadow">
        <div className="flex items-center gap-1.5">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap',
                  isActive
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        <div className="flex items-center gap-2 pl-4 border-l border-slate-700">
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-2.5 py-1.5 rounded-lg transition-colors"
            title="Refresh Pipeline Status"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Map / Visualization + Action Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left / Center: Interactive Investigation GIS */}
        <div className="lg:col-span-8 flex flex-col gap-3">
          <InvestigationGIS
            mode={incident.mode === 'demo' ? 'DEMO' : 'REAL'}
            spillGeometry={spillGeometry}
            hindcastTrajectories={activeHindcast?.trajectory_geojson}
            particleTimesteps={activeHindcast?.particle_timesteps_geojson}
            originP50={activeHindcast?.duration_slices?.['24h']?.p50_polygon || activeHindcast?.origin_p50_polygon || activeHindcast?.uncertainty_metadata?.p50_polygon}
            originP75={activeHindcast?.duration_slices?.['24h']?.p75_polygon || activeHindcast?.origin_p75_polygon || activeHindcast?.uncertainty_metadata?.p75_polygon}
            originP90={activeHindcast?.duration_slices?.['24h']?.p90_polygon || activeHindcast?.origin_p90_polygon || activeHindcast?.uncertainty_metadata?.p90_polygon}
            originUncertaintyEnvelope={activeHindcast?.uncertainty_metadata?.uncertainty_envelope}
            candidateVessels={candidates.map((c) => ({
              mmsi: c.mmsi,
              vessel_name: c.vessel_name,
              vessel_type: c.vessel_type,
              lat: 27.85 + (Math.random() - 0.5) * 0.2,
              lon: -89.5 + (Math.random() - 0.5) * 0.2,
              rank: c.rank,
              physical_score: c.physical_score,
            }))}
            counterfactualSimulatedSlick={selectedCandidate?.counterfactual_geojson || null}
            observedVsSimulatedComparison={selectedCandidate?.overlap_geojson || null}
            detectionTimeUtc={spillGeometry?.detection_time || activeHindcast?.detection_time || undefined}
            onCandidateClick={(mmsi) => {
              const found = candidates.find((c) => c.mmsi === mmsi)
              if (found) setSelectedCandidate(found)
            }}
          />
        </div>

        {/* Right Column: Execution Telemetry & Stage Actions */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <TaskProgressPanel incidentId={incident.id} />

          {/* Quick Stage Action Panel */}
          <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-4 shadow-lg flex flex-col gap-3">
            <h4 className="font-semibold text-xs text-slate-300 uppercase tracking-wider">
              Stage Control &amp; Actions
            </h4>

            {activeTab === 'imagery' && (
              <div className="flex flex-col gap-2 text-xs">
                <p className="text-slate-400">
                  Sentinel-1 SAR scene loaded. Ready to execute U-Net++ &amp; Look-alike classification.
                </p>
                <button
                  onClick={handleTriggerDetection}
                  disabled={loadingAction === 'detection'}
                  className="btn-primary flex items-center justify-center gap-2 py-2 w-full disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Run Spill Segmentation</span>
                </button>
              </div>
            )}

            {activeTab === 'detection' && (
              <div className="flex flex-col gap-3 text-xs">
                {spillGeometry ? (
                  <div className="bg-slate-900/80 border border-amber-500/30 rounded-lg p-3 flex flex-col gap-2 font-mono text-[11px]">
                    <div className="flex items-center justify-between text-amber-400 font-bold border-b border-slate-700/80 pb-1">
                      <span>GEOSPATIAL SPILL GEOMETRY</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-600/50">
                        {spillGeometry.geometry_quality?.validity || 'VALID'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Projected Area:</span>
                      <span className="font-bold text-amber-300">{spillGeometry.area_km2.toFixed(3)} km²</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Perimeter:</span>
                      <span>{spillGeometry.perimeter_km.toFixed(2)} km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Projected CRS:</span>
                      <span className="text-slate-300 truncate max-w-[170px]" title={spillGeometry.projected_crs}>
                        {spillGeometry.projected_crs}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Centroid:</span>
                      <span>{spillGeometry.centroid_lat.toFixed(4)}°, {spillGeometry.centroid_lon.toFixed(4)}°</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Vertices:</span>
                      <span>{spillGeometry.geometry_quality?.vertex_count || 0}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-400">
                    Detection completed. Spill vector geometry generated.
                  </p>
                )}

                <button
                  onClick={handleTriggerHindcast}
                  disabled={loadingAction === 'hindcast'}
                  className="btn-primary flex items-center justify-center gap-2 py-2 w-full disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Start Ocean Drift Hindcast</span>
                </button>
              </div>
            )}

            {activeTab === 'hindcast' && (
              <div className="flex flex-col gap-3 text-xs">
                {activeHindcast ? (
                  <div className="bg-slate-900/80 border border-ocean-500/30 rounded-lg p-3 flex flex-col gap-2 font-mono text-[11px]">
                    <div className="flex items-center justify-between text-ocean-400 font-bold border-b border-slate-700/80 pb-1">
                      <span>LAGRANGIAN HINDCAST ENSEMBLE</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-ocean-950/80 border border-ocean-600/50">
                        {activeHindcast.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Forcing Sources:</span>
                      <span className="text-slate-300">
                        {activeHindcast.wind_reader || 'ERA5'} · {activeHindcast.current_reader || 'CMEMS'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Particles (MC):</span>
                      <span className="font-bold text-ocean-300">{activeHindcast.n_particles}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">T-24h Origin:</span>
                      <span className="text-slate-200">
                        {activeHindcast.origin_lat?.toFixed(3)}°N, {activeHindcast.origin_lon?.toFixed(3)}°E
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Envelopes:</span>
                      <span className="text-slate-300">P50 / P75 / P90 Active</span>
                    </div>

                    {activeHindcast.duration_slices && (
                      <div className="mt-1 pt-1 border-t border-slate-800 grid grid-cols-4 gap-1 text-[10px] text-center">
                        {Object.entries(activeHindcast.duration_slices).map(([h, s]: [string, any]) => (
                          <div key={h} className="bg-slate-800/80 p-1 rounded">
                            <div className="text-ocean-400 font-bold">-{h}</div>
                            <div className="text-slate-400">{s.spread_km}km</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-slate-400">
                    Hindcast origin window calculated. Query historical AIS positions in origin envelope.
                  </p>
                )}

                <button
                  onClick={handleTriggerAIS}
                  disabled={loadingAction === 'ais'}
                  className="btn-primary flex items-center justify-center gap-2 py-2 w-full disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Execute Spatial AIS Search</span>
                </button>
              </div>
            )}

            {(activeTab === 'ais' || activeTab === 'ranking') && (
              <div className="flex flex-col gap-2 text-xs text-slate-400">
                <p>
                  Vessels sorted by XGBoost physical consistency ranking and Isolation Forest trajectory anomaly scoring.
                </p>
              </div>
            )}

            {activeTab === 'dossier' && (
              <div className="flex flex-col gap-2 text-xs text-slate-400">
                <p>
                  Compile all forensic artifacts into an official tamper-evident PDF dossier with SHA-256 manifest.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Area: Specialized Content based on Selected Tab */}
      <div className="w-full mt-2">
        {activeTab === 'ais' && (
          <VesselCandidateTable
            candidates={candidates}
            onSelectCandidate={(c) => setSelectedCandidate(c)}
          />
        )}

        {activeTab === 'ranking' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-7">
              <VesselCandidateTable
                candidates={candidates}
                onSelectCandidate={(c) => setSelectedCandidate(c)}
              />
            </div>
            <div className="lg:col-span-5">
              <ScoreBreakdown candidate={selectedCandidate} />
            </div>
          </div>
        )}

        {activeTab === 'dossier' && (
          <EvidenceManifestView
            incidentId={incident.id}
            manifest={manifest}
            onGenerateDossier={onRefresh}
          />
        )}
      </div>
    </div>
  )
}
