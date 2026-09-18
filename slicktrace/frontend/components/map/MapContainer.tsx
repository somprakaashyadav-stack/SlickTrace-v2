'use client'

import React, { useState, useRef } from 'react'
import { MapPin, Globe2, Compass, AlertCircle } from 'lucide-react'
import { MapControls } from './MapControls'
import { MapLegend, LegendItem } from './MapLegend'
import { LayerControl, MapLayer } from './LayerControl'
import { EmptyState } from '@/components/ui/EmptyState'

export interface MapContainerProps {
  center?: [number, number]
  zoom?: number
  layers?: MapLayer[]
  legendItems?: LegendItem[]
  hasGeometry?: boolean
  emptyMessage?: string
  children?: React.ReactNode
  className?: string
}

export function MapContainer({
  center = [25.5, 54.0], // default Gulf overview center if not specified
  zoom = 6,
  layers: initialLayers,
  legendItems,
  hasGeometry = false,
  emptyMessage = 'No investigation geometry available in REAL MODE. Upload or configure satellite imagery to populate spatial layers.',
  children,
  className = '',
}: MapContainerProps) {
  const [layers, setLayers] = useState<MapLayer[]>(
    initialLayers || [
      { id: 'satellite', label: 'Sentinel-1 SAR Scene', visible: true, color: '#38bdf8' },
      { id: 'segmentation', label: 'Oil Slick Segmentation Mask', visible: true, color: '#f87171' },
      { id: 'particles', label: 'Backward Lagrangian Particles', visible: true, color: '#fbbf24' },
      { id: 'origin_p90', label: 'Origin Probability (P90)', visible: true, color: '#0ea5e9' },
      { id: 'ais_tracks', label: 'AIS Vessel Trajectories', visible: true, color: '#34d399' },
      { id: 'counterfactual', label: 'Forward Verification Advection', visible: true, color: '#c084fc' },
    ]
  )
  const [layersOpen, setLayersOpen] = useState(false)
  const [legendOpen, setLegendOpen] = useState(true)

  const handleToggleLayer = (id: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l))
    )
  }

  return (
    <div
      className={`relative w-full h-[520px] rounded-2xl overflow-hidden border border-slate-800/90 bg-[#060b18] shadow-2xl flex flex-col justify-between select-none ${className}`}
    >
      {/* Bathymetric Grid Backdrop Pattern */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: `
            radial-gradient(circle at 50% 50%, rgba(14, 165, 233, 0.15) 0%, transparent 70%),
            linear-gradient(to right, rgba(30, 41, 59, 0.4) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(30, 41, 59, 0.4) 1px, transparent 1px)
          `,
          backgroundSize: '100% 100%, 40px 40px, 40px 40px',
        }}
      />

      {/* Top Map Header / Telemetry Bar */}
      <div className="relative z-20 flex items-center justify-between p-3 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80">
        <div className="flex items-center space-x-2 text-xs font-mono">
          <Globe2 className="w-4 h-4 text-sky-400" />
          <span className="font-semibold text-slate-200">GIS SPATIAL WORKSPACE</span>
          <span className="text-slate-400">|</span>
          <span className="text-slate-400">WGS84 / EPSG:4326</span>
        </div>
        <div className="flex items-center space-x-3 text-[11px] font-mono text-slate-400">
          <span>CENTER: [{center[0].toFixed(3)}°N, {center[1].toFixed(3)}°E]</span>
          <span>ZOOM: {zoom}x</span>
        </div>
      </div>

      {/* Map Body Content */}
      <div className="relative flex-1 w-full h-full flex items-center justify-center">
        {hasGeometry ? (
          <div className="w-full h-full relative z-10">{children}</div>
        ) : (
          <div className="relative z-10 max-w-md p-6">
            <EmptyState
              icon={MapPin}
              title="No Investigation Geometry"
              description={emptyMessage}
            />
          </div>
        )}

        {/* Floating Controls Overlay (Top Right) */}
        <div className="absolute top-3 right-3 z-30 flex flex-col items-end space-y-2">
          <MapControls
            onZoomIn={() => {}}
            onZoomOut={() => {}}
            onResetNorth={() => {}}
            onToggleLayers={() => setLayersOpen(!layersOpen)}
            layersOpen={layersOpen}
          />
          {layersOpen && (
            <LayerControl
              layers={layers}
              onToggleLayer={handleToggleLayer}
              onClose={() => setLayersOpen(false)}
            />
          )}
        </div>

        {/* Floating Legend Overlay (Bottom Left) */}
        {hasGeometry && (
          <div className="absolute bottom-3 left-3 z-30">
            <MapLegend items={legendItems} />
          </div>
        )}
      </div>

      {/* Bottom GIS Coordinate Bar */}
      <div className="relative z-20 px-3 py-1.5 bg-slate-950/90 border-t border-slate-800/80 text-[10px] font-mono text-slate-400 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-emerald-400 font-bold">CRS: EPSG:4326 / UTM-39N</span>
          <span>SCALE: 1:50,000</span>
        </div>
        <div className="text-slate-400">
          OpenDrift Lagrangian Particle Dispersion & MarineCadastre Historical AIS
        </div>
      </div>
    </div>
  )
}
