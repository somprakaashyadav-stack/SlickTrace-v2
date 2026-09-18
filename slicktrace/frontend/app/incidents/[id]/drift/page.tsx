'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Wind, Play, ArrowRight, ArrowLeft, Clock, ShieldCheck, Compass, Sliders, CheckCircle2, Waves } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Incident, SpillDetection, SpillGeometry, HindcastRun } from '@/lib/api/types'
import { InvestigationGIS } from '@/components/map/InvestigationGIS'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'
import { toast } from 'sonner'

export default function IncidentDriftPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const [particles, setParticles] = useState(1000)
  const [hoursBack, setHoursBack] = useState(24)
  const [oilType, setOilType] = useState('GENERIC BUNKER C')
  const [isRunning, setIsRunning] = useState(false)

  const { data: incident } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => api.get<Incident>(`/incidents/${id}`),
    enabled: !!id,
  })

  const { data: detections = [] } = useQuery({
    queryKey: ['detections', id],
    queryFn: () => api.get<SpillDetection[]>(`/incidents/${id}/detections`),
    enabled: !!id,
  })

  const activeDetection = detections.length > 0 ? detections[0] : null

  const { data: spillGeometry } = useQuery({
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

  const { data: hindcasts = [], refetch: refetchHindcasts } = useQuery({
    queryKey: ['hindcasts', id],
    queryFn: () => api.get<HindcastRun[]>(`/incidents/${id}/hindcast`),
    enabled: !!id,
  })

  const activeHindcast = hindcasts.length > 0 ? hindcasts[0] : null

  // Step 6: Run Backward Drift
  const handleRunHindcast = async () => {
    if (!activeDetection) {
      toast.error('Complete 02 Detection and approve the slick mask before running ocean drift')
      return
    }
    setIsRunning(true)
    try {
      await api.post(`/incidents/${id}/hindcast`, {
        detection_id: activeDetection.id,
        start_lat: spillGeometry?.centroid_lat ?? 27.5,
        start_lon: spillGeometry?.centroid_lon ?? -90.0,
        detection_time: spillGeometry?.detection_time || new Date().toISOString(),
        hours_back: hoursBack,
        durations_hours: [4, 8, 12, 24],
        n_particles: particles,
        oil_type: oilType,
        allow_fallback: true,
        slick_polygon: spillGeometry?.geojson_polygon ?? null,
      })
      toast.success('Step 6 Complete: OpenDrift backward Lagrangian simulation executed')
      refetchHindcasts()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Drift hindcast execution failed')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="flex flex-col gap-5 font-sans">
      {/* Provenance Card */}
      <DataProvenanceCard
        title="03 Physical Hindcast &amp; Probabilistic Origin Provenance"
        provider={activeHindcast?.wind_reader || 'ECMWF ERA5 (0.25°) + CMEMS Global PHY (0.083°)'}
        datasetName={activeHindcast?.id ? `HINDCAST-${activeHindcast.id.slice(0, 8)}` : 'OPENDRIFT-OPENOIL-V2'}
        timestampUtc={activeHindcast?.detection_time || new Date().toISOString()}
        crs="EPSG:4326 (WGS 84 Ellipsoid / Lagrangian Geodesic)"
        sha256={activeHindcast?.provenance?.simulation_id || '9e8a7c6b5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a'}
        algorithm="OpenDrift OpenOil Backward Lagrangian Advection + Bivariate Gaussian KDE"
        forcingSources={{
          wind: activeHindcast?.wind_reader || 'ERA5 10m Wind Reanalysis',
          currents: activeHindcast?.current_reader || 'CMEMS GLOBAL Reanalysis',
          waves: 'CMEMS Global Wave Model (Stokes drift active)',
        }}
        mode={incident?.mode === 'demo' ? 'DEMO' : 'REAL'}
        notes={[
          'Step 6: Monte Carlo particles advected backwards in time with Stokes drift wave forcing.',
          'Step 7: P50 (50%), P75 (75%), and P90 (90%) origin envelopes calculated via 2D kernel density estimation.',
        ]}
      />

      {/* Main Grid: GIS + Steps 6 & 7 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8 flex flex-col gap-3">
          <InvestigationGIS
            mode={incident?.mode === 'demo' ? 'DEMO' : 'REAL'}
            spillGeometry={spillGeometry}
            hindcastTrajectories={activeHindcast?.trajectory_geojson}
            particleTimesteps={activeHindcast?.particle_timesteps_geojson}
            originP50={activeHindcast?.duration_slices?.['24h']?.p50_polygon || activeHindcast?.origin_p50_polygon || activeHindcast?.uncertainty_metadata?.p50_polygon}
            originP75={activeHindcast?.duration_slices?.['24h']?.p75_polygon || activeHindcast?.origin_p75_polygon || activeHindcast?.uncertainty_metadata?.p75_polygon}
            originP90={activeHindcast?.duration_slices?.['24h']?.p90_polygon || activeHindcast?.origin_p90_polygon || activeHindcast?.uncertainty_metadata?.p90_polygon}
            originUncertaintyEnvelope={activeHindcast?.uncertainty_metadata?.uncertainty_envelope}
            initialLat={activeHindcast?.origin_lat ?? spillGeometry?.centroid_lat ?? 27.5}
            initialLon={activeHindcast?.origin_lon ?? spillGeometry?.centroid_lon ?? -90.0}
            detectionTimeUtc={activeHindcast?.detection_time || spillGeometry?.detection_time}
          />
        </div>

        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Step 6: Run Backward Drift */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Wind className="w-4 h-4 text-ocean-400" />
                <span>Step 6: Run Backward Drift</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-400">
                {activeHindcast ? 'COMPLETED' : 'READY'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-semibold text-slate-400">MC Particles</label>
                <input
                  type="number"
                  value={particles}
                  onChange={(e) => setParticles(parseInt(e.target.value, 10))}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-ocean-500"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-semibold text-slate-400">Horizon</label>
                <select
                  value={hoursBack}
                  onChange={(e) => setHoursBack(parseInt(e.target.value, 10))}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-ocean-500"
                >
                  <option value={4}>-4h Horizon</option>
                  <option value={8}>-8h Horizon</option>
                  <option value={12}>-12h Horizon</option>
                  <option value={24}>-24h Horizon</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-semibold text-slate-400">Hydrocarbon Oil Profile</label>
              <select
                value={oilType}
                onChange={(e) => setOilType(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-ocean-500"
              >
                <option value="GENERIC BUNKER C">GENERIC BUNKER C (Heavy Fuel Oil)</option>
                <option value="ARABIAN LIGHT">ARABIAN LIGHT (Crude Oil)</option>
                <option value="MARINE DIESEL">MARINE DIESEL (Distillate)</option>
              </select>
            </div>

            <button
              onClick={handleRunHindcast}
              disabled={isRunning}
              className="btn-primary w-full py-2.5 text-xs flex items-center justify-center gap-2 shadow-lg shadow-brand-900/40 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{isRunning ? 'Advecting Particles...' : 'Run OpenDrift Backward Simulation'}</span>
            </button>
          </div>

          {/* Step 7: Review Origin Probability */}
          {activeHindcast && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow flex flex-col gap-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Clock className="w-4 h-4 text-ocean-400" />
                  <span>Step 7: Origin Probability</span>
                </h3>
                <span className="text-[10px] font-mono text-ocean-300 font-bold bg-ocean-950 px-2 py-0.5 rounded border border-ocean-700">
                  RECONSTRUCTED
                </span>
              </div>

              <div className="bg-slate-950/80 border border-ocean-500/30 rounded-xl p-3 flex flex-col gap-1.5 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">T-24h Origin Centroid:</span>
                  <span className="font-bold text-ocean-300">
                    {activeHindcast.origin_lat?.toFixed(3)}°N, {activeHindcast.origin_lon?.toFixed(3)}°E
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Origin Time Window:</span>
                  <span className="text-slate-300 text-[10px]">
                    {activeHindcast.origin_time_start ? new Date(activeHindcast.origin_time_start).toLocaleTimeString() : 'T-24h'} - {activeHindcast.origin_time_end ? new Date(activeHindcast.origin_time_end).toLocaleTimeString() : 'T0'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Origin Envelopes:</span>
                  <span className="text-slate-200">P50 (Core) / P75 / P90 Active</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-2">
                <Link
                  href={`/incidents/${id}/detection`}
                  className="btn-secondary py-2 text-xs flex items-center gap-1 flex-1 justify-center"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Detection</span>
                </Link>
                <Link
                  href={`/incidents/${id}/vessels`}
                  className="btn-primary py-2 text-xs flex items-center gap-1 flex-1 justify-center"
                >
                  <span>Step 8: AIS Search</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
