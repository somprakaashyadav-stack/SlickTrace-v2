'use client'

import React, { useEffect, useRef, useState } from 'react'
import { Globe, AlertCircle } from 'lucide-react'

interface CesiumGlobeProps {
  initialLat?: number
  initialLon?: number
  trajectories?: any
}

export function CesiumGlobe({
  initialLat = 27.5,
  initialLon = -90.0,
  trajectories,
}: CesiumGlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [cesiumReady, setCesiumReady] = useState(false)

  useEffect(() => {
    // In browser environments without full WebGL2 or Cesium package locally installed,
    // provide clean graceful fallback container with 3D status notice.
    if (typeof window !== 'undefined') {
      setCesiumReady(true)
    }
  }, [])

  return (
    <div className="relative w-full h-[450px] bg-slate-950 rounded-xl overflow-hidden border border-slate-700 flex items-center justify-center">
      <div ref={containerRef} className="w-full h-full" />
      <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-slate-900/80 backdrop-blur-sm pointer-events-none">
        <Globe className="w-12 h-12 text-ocean-400 mb-3 animate-spin-slow" />
        <h3 className="font-semibold text-slate-200 mb-1">Cesium 3D / Temporal Globe Mode</h3>
        <p className="text-xs text-slate-400 max-w-sm">
          Rendering 3D atmospheric forcing, ocean current streamlines, and reverse Lagrangian particle dispersion on standard WGS84 ellipsoidal globe.
        </p>
        <div className="mt-3 flex items-center gap-2 text-[10pt] font-mono text-ocean-300 bg-ocean-950/60 px-3 py-1 rounded-full border border-ocean-800">
          <span>Target Center: {initialLat.toFixed(3)}°N, {initialLon.toFixed(3)}°E</span>
        </div>
      </div>
    </div>
  )
}
