'use client'

import React, { useState, useMemo } from 'react'
import {
  Layers,
  Eye,
  EyeOff,
  Sliders,
  Globe2,
  Map as MapIcon,
  Mountain,
  Compass,
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Clock,
  Info,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Sparkles,
} from 'lucide-react'
import { MapboxScene, MapboxSceneProps } from './MapboxScene'
import { CesiumGlobe } from './CesiumGlobe'
import { cn } from '@/lib/utils'

export interface LayerState {
  id: string
  name: string
  category: 'satellite' | 'segmentation' | 'hindcast' | 'ais' | 'counterfactual'
  visible: boolean
  opacity: number
  mode: 'REAL' | 'DEMO'
  color: string
  description: string
}

export interface InvestigationGISProps extends MapboxSceneProps {
  detectionTimeUtc?: string
  onCandidateClick?: (mmsi: string) => void
}

const DEFAULT_LAYERS: LayerState[] = [
  {
    id: 'satellite_raster',
    name: '1. Satellite Raster (Sentinel-1 SAR)',
    category: 'satellite',
    visible: true,
    opacity: 0.85,
    mode: 'REAL',
    color: '#94a3b8',
    description: 'Calibrated SAR backscatter / optical ortho-rectified imagery',
  },
  {
    id: 'oil_detection_mask',
    name: '2. Oil Detection Mask (U-Net++)',
    category: 'segmentation',
    visible: true,
    opacity: 0.6,
    mode: 'REAL',
    color: '#f59e0b',
    description: 'Neural segmentation probability heatmap',
  },
  {
    id: 'oil_polygon',
    name: '3. Oil Spill Polygon (Vector)',
    category: 'segmentation',
    visible: true,
    opacity: 0.8,
    mode: 'REAL',
    color: '#d97706',
    description: 'Topologically validated polygon with projected area & centroid',
  },
  {
    id: 'lookalike_regions',
    name: '4. Look-Alike Regions',
    category: 'segmentation',
    visible: true,
    opacity: 0.5,
    mode: 'REAL',
    color: '#10b981',
    description: 'Classified false positives (algae, ship wakes, low wind)',
  },
  {
    id: 'backward_particles',
    name: '5. Backward Particles (OpenDrift)',
    category: 'hindcast',
    visible: true,
    opacity: 0.85,
    mode: 'REAL',
    color: '#06b6d4',
    description: 'Lagrangian Monte Carlo particles drifted reverse in time',
  },
  {
    id: 'origin_probability',
    name: '6. Origin Probability (P50 / P75 / P90)',
    category: 'hindcast',
    visible: true,
    opacity: 0.7,
    mode: 'REAL',
    color: '#ec4899',
    description: 'Bivariate kernel density envelopes of probable spill origins',
  },
  {
    id: 'origin_uncertainty',
    name: '7. Origin Uncertainty Envelope',
    category: 'hindcast',
    visible: true,
    opacity: 0.45,
    mode: 'REAL',
    color: '#64748b',
    description: 'Environmental forcing variance & Stokes drift uncertainty buffer',
  },
  {
    id: 'ais_vessel_points',
    name: '8. AIS Vessel Points',
    category: 'ais',
    visible: true,
    opacity: 0.9,
    mode: 'REAL',
    color: '#38bdf8',
    description: 'Observed historical AIS broadcast points in search envelope',
  },
  {
    id: 'ais_vessel_tracks',
    name: '9. AIS Vessel Tracks',
    category: 'ais',
    visible: true,
    opacity: 0.65,
    mode: 'REAL',
    color: '#0ea5e9',
    description: 'Interpolated historical kinematics & course trajectories',
  },
  {
    id: 'candidate_vessel_tracks',
    name: '10. Candidate Vessel Attribution Tracks',
    category: 'ais',
    visible: true,
    opacity: 0.95,
    mode: 'REAL',
    color: '#ef4444',
    description: 'Ranked candidate vessels with physical consistency score',
  },
  {
    id: 'counterfactual_simulated_slick',
    name: '11. Counterfactual Simulated Slick',
    category: 'counterfactual',
    visible: true,
    opacity: 0.75,
    mode: 'REAL',
    color: '#8b5cf6',
    description: 'Forward OpenDrift simulation from candidate release position',
  },
  {
    id: 'observed_vs_simulated_comparison',
    name: '12. Observed vs Simulated Overlap (IoU)',
    category: 'counterfactual',
    visible: true,
    opacity: 0.85,
    mode: 'REAL',
    color: '#10b981',
    description: 'Geometric intersection and IoU consistency verification',
  },
]

export function InvestigationGIS(props: InvestigationGISProps) {
  const {
    initialLat = 27.5,
    initialLon = -90.0,
    initialZoom = 8,
    mode = 'REAL',
    detectionTimeUtc,
    candidateVessels = [],
    onCandidateClick,
  } = props

  // State
  const [viewDimension, setViewDimension] = useState<'2d' | '3d'>('2d')
  const [basemapStyle, setBasemapStyle] = useState<'dark' | 'satellite' | 'streets' | 'outdoors'>('dark')
  const [enableTerrain, setEnableTerrain] = useState<boolean>(false)
  const [layers, setLayers] = useState<LayerState[]>(
    DEFAULT_LAYERS.map((l) => ({ ...l, mode }))
  )
  const [layersOpen, setLayersOpen] = useState(true)
  const [legendOpen, setLegendOpen] = useState(true)

  // Timeline / Particle Step State
  const [currentHour, setCurrentHour] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1)
  const totalHours = 24
  const durationPresets = [4, 8, 12, 24]

  // Telemetry Coordinates
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lon: number; zoom: number }>({
    lat: initialLat,
    lon: initialLon,
    zoom: initialZoom,
  })

  // Layer Config Record for MapboxScene
  const layerConfigs = useMemo(() => {
    const map: Record<string, { visible: boolean; opacity: number }> = {}
    layers.forEach((l) => {
      map[l.id] = { visible: l.visible, opacity: l.opacity }
    })
    return map
  }, [layers])

  // Toggle Layer Visibility
  const toggleLayerVisibility = (layerId: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, visible: !l.visible } : l))
    )
  }

  // Set Layer Opacity
  const setLayerOpacity = (layerId: string, opacity: number) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, opacity } : l))
    )
  }

  // Animation Interval
  React.useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    if (isPlaying) {
      const delay = Math.max(150, Math.round(700 / playbackSpeed))
      interval = setInterval(() => {
        setCurrentHour((prev) => {
          const next = prev + 1
          if (next > totalHours) {
            setIsPlaying(false)
            return totalHours
          }
          return next
        })
      }, delay)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isPlaying, totalHours, playbackSpeed])

  // Calculate Timestamp for current animation hour
  const currentTimestampStr = useMemo(() => {
    const base = detectionTimeUtc ? new Date(detectionTimeUtc) : new Date()
    const offsetMs = currentHour * 3600 * 1000
    const target = new Date(base.getTime() - offsetMs)
    return target.toISOString().replace('T', ' ').replace('.000Z', ' UTC')
  }, [detectionTimeUtc, currentHour])

  return (
    <div className="relative w-full h-[620px] rounded-2xl overflow-hidden border border-slate-700/80 bg-slate-950 shadow-2xl flex flex-col font-sans">
      {/* 1. TOP HEADER TOOLBAR */}
      <div className="absolute top-3 left-3 right-3 z-20 flex items-center justify-between gap-3 pointer-events-none">
        {/* Left: GIS Title & Mode Badge */}
        <div className="flex items-center gap-2.5 bg-slate-900/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-slate-700/80 shadow-lg pointer-events-auto">
          <Compass className="w-4 h-4 text-ocean-400" />
          <span className="text-xs font-bold text-slate-100 tracking-wide">
            INVESTIGATION GIS
          </span>
          <div className="h-3 w-[1px] bg-slate-700" />
          {mode === 'REAL' ? (
            <span className="flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-950/90 text-emerald-300 border border-emerald-600/50">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              REAL MODE
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-amber-950/90 text-amber-300 border border-amber-600/50">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              DEMO MODE
            </span>
          )}
        </div>

        {/* Right: View Controls (2D/3D, Basemap, Terrain, Layer Panel Toggle) */}
        <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur-md p-1.5 rounded-xl border border-slate-700/80 shadow-lg pointer-events-auto">
          {/* 2D / 3D Mode Toggle */}
          <div className="flex items-center bg-slate-800/90 rounded-lg p-0.5 border border-slate-700">
            <button
              onClick={() => setViewDimension('2d')}
              className={cn(
                'flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors',
                viewDimension === '2d'
                  ? 'bg-ocean-600 text-white font-semibold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              <MapIcon className="w-3.5 h-3.5" />
              <span>2D Map</span>
            </button>
            <button
              onClick={() => setViewDimension('3d')}
              className={cn(
                'flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors',
                viewDimension === '3d'
                  ? 'bg-ocean-600 text-white font-semibold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              <Globe2 className="w-3.5 h-3.5" />
              <span>3D Globe</span>
            </button>
          </div>

          {/* Basemap Selector */}
          {viewDimension === '2d' && (
            <select
              value={basemapStyle}
              onChange={(e) => setBasemapStyle(e.target.value as any)}
              className="bg-slate-800 text-slate-200 text-[11px] font-medium px-2.5 py-1 rounded-lg border border-slate-700 focus:outline-none focus:border-ocean-500"
            >
              <option value="dark">Dark Canvas</option>
              <option value="satellite">Satellite Ortho</option>
              <option value="streets">Maritime Streets</option>
              <option value="outdoors">Bathymetry / Relief</option>
            </select>
          )}

          {/* 3D Terrain Toggle */}
          {viewDimension === '2d' && (
            <button
              onClick={() => setEnableTerrain(!enableTerrain)}
              className={cn(
                'flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-colors',
                enableTerrain
                  ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
              )}
              title="Toggle 3D Elevation / Terrain DEM"
            >
              <Mountain className="w-3.5 h-3.5" />
              <span>3D Terrain</span>
            </button>
          )}

          {/* Layer Panel Button */}
          <button
            onClick={() => setLayersOpen(!layersOpen)}
            className={cn(
              'flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-colors',
              layersOpen
                ? 'bg-ocean-950/80 border-ocean-500/50 text-ocean-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
            )}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Layers ({layers.filter((l) => l.visible).length}/{layers.length})</span>
          </button>
        </div>
      </div>

      {/* 2. MAIN MAP / GLOBE VIEW */}
      <div className="flex-1 w-full h-full relative">
        {viewDimension === '2d' ? (
          <MapboxScene
            {...props}
            basemapStyle={basemapStyle}
            enableTerrain={enableTerrain}
            layerConfigs={layerConfigs}
            currentHour={currentHour}
            onCoordinatesChange={setCursorCoords}
            onVesselSelect={(mmsi) => {
              if (onCandidateClick) onCandidateClick(mmsi)
              if (props.onVesselSelect) props.onVesselSelect(mmsi)
            }}
          />
        ) : (
          <CesiumGlobe
            initialLat={initialLat}
            initialLon={initialLon}
            trajectories={props.hindcastTrajectories}
          />
        )}
      </div>

      {/* 3. FLOATING COLLAPSIBLE LAYER MANAGEMENT PANEL */}
      {layersOpen && (
        <div className="absolute top-16 left-3 w-80 max-h-[440px] bg-slate-900/95 backdrop-blur-md rounded-xl border border-slate-700/90 shadow-2xl p-3.5 z-20 flex flex-col gap-2 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-ocean-400" />
              <span className="text-xs font-bold text-slate-200">INVESTIGATION LAYERS</span>
            </div>
            <button
              onClick={() => setLayersOpen(false)}
              className="text-slate-400 hover:text-slate-200 p-1 rounded"
            >
              <ChevronUp className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex flex-col gap-2 divide-y divide-slate-800/60">
            {layers.map((layer) => (
              <div key={layer.id} className="pt-2 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={layer.visible}
                      onChange={() => toggleLayerVisibility(layer.id)}
                      className="w-3.5 h-3.5 rounded bg-slate-800 border-slate-600 text-ocean-600 focus:ring-ocean-500 cursor-pointer"
                    />
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: layer.color }}
                    />
                    <span
                      className={cn(
                        'text-[11px] font-medium leading-tight',
                        layer.visible ? 'text-slate-200 font-semibold' : 'text-slate-500 line-through'
                      )}
                    >
                      {layer.name}
                    </span>
                  </label>

                  {/* REAL / DEMO Indicator Badge */}
                  <span
                    className={cn(
                      'text-[9px] font-mono px-1.5 py-0.5 rounded font-bold uppercase tracking-wider',
                      layer.mode === 'REAL'
                        ? 'bg-emerald-950/90 text-emerald-300 border border-emerald-700/50'
                        : 'bg-amber-950/90 text-amber-300 border border-amber-700/50'
                    )}
                  >
                    {layer.mode}
                  </span>
                </div>

                {/* Layer Opacity Slider */}
                {layer.visible && (
                  <div className="flex items-center gap-2 pl-6 pr-1 mt-0.5">
                    <Sliders className="w-3 h-3 text-slate-500" />
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={layer.opacity}
                      onChange={(e) => setLayerOpacity(layer.id, parseFloat(e.target.value))}
                      className="w-full h-1 bg-slate-700 rounded appearance-none cursor-pointer accent-ocean-400"
                    />
                    <span className="text-[10px] font-mono text-slate-400 w-7 text-right">
                      {Math.round(layer.opacity * 100)}%
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. FLOATING COLLAPSIBLE LEGEND PANEL */}
      <div className="absolute top-16 right-3 z-20">
        {legendOpen ? (
          <div className="w-64 bg-slate-900/95 backdrop-blur-md rounded-xl border border-slate-700/90 shadow-2xl p-3 flex flex-col gap-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
              <div className="flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-[11px] font-bold text-slate-200">MAP LEGEND</span>
              </div>
              <button
                onClick={() => setLegendOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-0.5"
              >
                <ChevronUp className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-1.5 text-[10px] text-slate-300">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#d97706] border border-[#f59e0b]" />
                <span>Observed Oil Spill (SAR Mask)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#10b981] border border-[#34d399]" />
                <span>Algae-like Look-alike</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#06b6d4] border border-[#38bdf8]" />
                <span>Ship Wake Dark Area</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#8b5cf6] border border-[#a78bfa]" />
                <span>Low Wind Calm Area</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#06b6d4] shadow-sm" />
                <span>OpenDrift Backward Particles</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#ec4899]/70 border border-[#f43f5e]" />
                <span>P50 Origin Envelope (Core)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#6366f1]/50 border border-[#818cf8]" />
                <span>P75 Origin Envelope</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#3b82f6]/30 border border-[#60a5fa]" />
                <span>P90 Origin Envelope</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ef4444] border border-white" />
                <span>Candidate Vessel (AIS Evidence)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#8b5cf6]/60 border border-[#a78bfa] border-dashed" />
                <span>Counterfactual Forward Slick</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#10b981]/70 border border-[#34d399]" />
                <span>Observed vs Sim Overlap (IoU)</span>
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setLegendOpen(true)}
            className="flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700 shadow-lg text-[11px] font-medium text-slate-300 hover:text-white"
          >
            <Info className="w-3.5 h-3.5 text-amber-400" />
            <span>Show Legend</span>
          </button>
        )}
      </div>

      {/* 5. BOTTOM TIMELINE & ANIMATION CONTROLS BAR */}
      <div className="absolute bottom-9 left-3 right-3 z-20 bg-slate-900/95 backdrop-blur-md border border-slate-700/90 rounded-xl p-2.5 shadow-2xl flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-slate-300">
          {/* Left: Playback Telemetry */}
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-ocean-400" />
            <span className="font-bold text-slate-100">Lagrangian Backward Dispersion</span>
            <span className="font-mono text-ocean-300 bg-ocean-950/80 px-2 py-0.5 rounded border border-ocean-700/60 text-[11px] font-semibold">
              T - {currentHour}h ({currentHour === 0 ? 'Spill Detection' : 'Simulated Hindcast Origin'})
            </span>
            <span className="text-slate-400 font-mono text-[10px] hidden sm:inline">
              [{currentTimestampStr}]
            </span>
          </div>

          {/* Right: Horizon Presets */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Horizon:</span>
            <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700">
              {durationPresets.map((d) => (
                <button
                  key={d}
                  onClick={() => setCurrentHour(d)}
                  className={cn(
                    'px-2 py-0.5 text-[10px] font-mono rounded transition-colors',
                    currentHour === d
                      ? 'bg-ocean-600 text-white font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  )}
                >
                  -{d}h
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Playback Controls & Slider */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors shadow"
            title={isPlaying ? 'Pause Animation' : 'Play Dispersion Animation'}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={() => {
              setIsPlaying(false)
              setCurrentHour(0)
            }}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
            title="Reset to T0 (Spill Detection Time)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Time Slider */}
          <input
            type="range"
            min="0"
            max={totalHours}
            value={currentHour}
            onChange={(e) => setCurrentHour(parseInt(e.target.value, 10))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-ocean-400 border border-slate-700"
          />

          {/* Playback Speed */}
          <button
            onClick={() => setPlaybackSpeed(playbackSpeed === 1 ? 2 : playbackSpeed === 2 ? 5 : 1)}
            className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-mono flex items-center gap-1 border border-slate-700"
            title="Playback Speed"
          >
            <FastForward className="w-3 h-3 text-ocean-400" />
            <span>{playbackSpeed}x</span>
          </button>

          <span className="text-xs font-mono text-slate-400 flex-shrink-0">
            -24h
          </span>
        </div>
      </div>

      {/* 6. LIVE STATUS & TELEMETRY FOOTER */}
      <div className="h-7 bg-slate-950 border-t border-slate-800 px-4 flex items-center justify-between text-[10px] font-mono text-slate-400 select-none z-10">
        <div className="flex items-center gap-4">
          <span>LAT: <strong className="text-slate-200">{cursorCoords.lat.toFixed(5)}°</strong></span>
          <span>LON: <strong className="text-slate-200">{cursorCoords.lon.toFixed(5)}°</strong></span>
          <span>ZOOM: <strong className="text-slate-200">{cursorCoords.zoom.toFixed(1)}</strong></span>
          <span className="hidden sm:inline">CRS: <strong className="text-slate-300">WGS 84 (EPSG:4326)</strong></span>
        </div>

        <div className="flex items-center gap-3">
          {candidateVessels.length > 0 && (
            <span className="text-amber-400 font-semibold">
              {candidateVessels.length} Candidate Vessels Under Investigation
            </span>
          )}
          <span className="text-slate-500">|</span>
          <span className="text-slate-400">SlickTrace GIS Engine v2.0</span>
        </div>
      </div>
    </div>
  )
}
