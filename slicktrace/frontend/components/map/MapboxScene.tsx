'use client'

import React, { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { SpillGeometry } from '@/lib/api/types'

export interface MapLayerConfig {
  id: string
  name: string
  visible: boolean
  opacity: number
  mode: 'REAL' | 'DEMO'
  color: string
  description: string
}

export interface MapboxSceneProps {
  initialLat?: number
  initialLon?: number
  initialZoom?: number
  mode?: 'REAL' | 'DEMO'

  // 1. Satellite raster & mask
  satelliteRasterUrl?: string
  satelliteRasterBounds?: [number, number, number, number] // [minLon, minLat, maxLon, maxLat]
  detectionMaskUrl?: string

  // 2. Oil polygon & look-alikes
  spillPolygon?: any
  spillGeometry?: SpillGeometry | null
  lookalikeRegions?: any // GeoJSON FeatureCollection

  // 3. Backward hindcast particles & probability
  hindcastTrajectories?: any
  particleTimesteps?: any
  currentHour?: number
  originP50?: any
  originP75?: any
  originP90?: any
  originUncertaintyEnvelope?: any

  // 4. AIS & candidates
  aisVesselPoints?: any // GeoJSON FeatureCollection
  aisVesselTracks?: any // GeoJSON FeatureCollection
  candidateVessels?: Array<{
    mmsi: string
    vessel_name?: string
    vessel_type?: string
    lat: number
    lon: number
    rank?: number
    physical_score?: number
    track_geometry?: any
  }>

  // 5. Counterfactual verification
  counterfactualSimulatedSlick?: any
  observedVsSimulatedComparison?: any // Overlap polygon with IoU metrics

  // Controls & visibility
  layerConfigs?: Record<string, { visible: boolean; opacity: number }>
  basemapStyle?: 'satellite' | 'dark' | 'streets' | 'outdoors'
  enableTerrain?: boolean

  // Callbacks
  onVesselSelect?: (mmsi: string) => void
  onCoordinatesChange?: (coords: { lat: number; lon: number; zoom: number }) => void
}

export function MapboxScene({
  initialLat = 27.5,
  initialLon = -90.0,
  initialZoom = 8,
  mode = 'REAL',
  satelliteRasterUrl,
  satelliteRasterBounds,
  detectionMaskUrl,
  spillPolygon,
  spillGeometry,
  lookalikeRegions,
  hindcastTrajectories,
  particleTimesteps,
  currentHour = 0,
  originP50,
  originP75,
  originP90,
  originUncertaintyEnvelope,
  aisVesselPoints,
  aisVesselTracks,
  candidateVessels = [],
  counterfactualSimulatedSlick,
  observedVsSimulatedComparison,
  layerConfigs = {},
  basemapStyle = 'dark',
  enableTerrain = false,
  onVesselSelect,
  onCoordinatesChange,
}: MapboxSceneProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ''

  // Initialize Mapbox map
  useEffect(() => {
    if (!mapContainer.current) return
    if (!token) return

    mapboxgl.accessToken = token

    const styleUri = {
      satellite: 'mapbox://styles/mapbox/satellite-v9',
      dark: 'mapbox://styles/mapbox/dark-v11',
      streets: 'mapbox://styles/mapbox/streets-v12',
      outdoors: 'mapbox://styles/mapbox/outdoors-v12',
    }[basemapStyle] || 'mapbox://styles/mapbox/dark-v11'

    const instance = new mapboxgl.Map({
      container: mapContainer.current,
      style: styleUri,
      center: [initialLon, initialLat],
      zoom: initialZoom,
      attributionControl: false,
    })

    instance.addControl(new mapboxgl.NavigationControl({ showCompass: true }), 'bottom-right')
    instance.addControl(new mapboxgl.ScaleControl({ unit: 'nautical' }), 'bottom-left')

    instance.on('load', () => {
      map.current = instance
      setMapLoaded(true)

      // Add DEM terrain if requested
      if (enableTerrain) {
        try {
          instance.addSource('mapbox-dem', {
            type: 'raster-dem',
            url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
            tileSize: 512,
            maxzoom: 14,
          })
          instance.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })
        } catch {
          // Ignore if already added
        }
      }
    })

    instance.on('mousemove', (e) => {
      if (onCoordinatesChange) {
        onCoordinatesChange({
          lat: e.lngLat.lat,
          lon: e.lngLat.lng,
          zoom: instance.getZoom(),
        })
      }
    })

    return () => {
      instance.remove()
      map.current = null
    }
  }, [token, basemapStyle, enableTerrain])

  // Helper to get layer opacity and visibility
  const getLayerState = (layerKey: string, defaultVisible = true, defaultOpacity = 1.0) => {
    const cfg = layerConfigs[layerKey]
    return {
      visible: cfg ? cfg.visible : defaultVisible,
      opacity: cfg ? cfg.opacity : defaultOpacity,
    }
  }

  // Update All 12 Layers when map is loaded or props update
  useEffect(() => {
    if (!map.current || !mapLoaded) return
    const m = map.current

    // Helper to add or update GeoJSON source
    const setGeoJSONSource = (sourceId: string, data: any) => {
      if (!data) return false
      const source = m.getSource(sourceId) as mapboxgl.GeoJSONSource
      if (source) {
        source.setData(data)
        return true
      }
      m.addSource(sourceId, { type: 'geojson', data })
      return true
    }

    // 1. SATELLITE RASTER & DETECTION MASK
    const satState = getLayerState('satellite_raster', true, 0.85)
    if (satelliteRasterUrl && satelliteRasterBounds && satelliteRasterBounds.length === 4) {
      const [w, s, e, n] = satelliteRasterBounds
      const coords: [[number, number], [number, number], [number, number], [number, number]] = [
        [w, n],
        [e, n],
        [e, s],
        [w, s],
      ]
      if (m.getSource('satellite-raster-source')) {
        m.setLayoutProperty('satellite-raster-layer', 'visibility', satState.visible ? 'visible' : 'none')
        m.setPaintProperty('satellite-raster-layer', 'raster-opacity', satState.opacity)
      } else {
        m.addSource('satellite-raster-source', {
          type: 'image',
          url: satelliteRasterUrl,
          coordinates: coords,
        })
        m.addLayer({
          id: 'satellite-raster-layer',
          type: 'raster',
          source: 'satellite-raster-source',
          paint: { 'raster-opacity': satState.opacity },
          layout: { visibility: satState.visible ? 'visible' : 'none' },
        })
      }
    }

    // 2. OIL DETECTION MASK
    const maskState = getLayerState('oil_detection_mask', true, 0.6)
    if (detectionMaskUrl && satelliteRasterBounds && satelliteRasterBounds.length === 4) {
      const [w, s, e, n] = satelliteRasterBounds
      const coords: [[number, number], [number, number], [number, number], [number, number]] = [
        [w, n],
        [e, n],
        [e, s],
        [w, s],
      ]
      if (m.getSource('detection-mask-source')) {
        m.setLayoutProperty('detection-mask-layer', 'visibility', maskState.visible ? 'visible' : 'none')
        m.setPaintProperty('detection-mask-layer', 'raster-opacity', maskState.opacity)
      } else {
        m.addSource('detection-mask-source', {
          type: 'image',
          url: detectionMaskUrl,
          coordinates: coords,
        })
        m.addLayer({
          id: 'detection-mask-layer',
          type: 'raster',
          source: 'detection-mask-source',
          paint: { 'raster-opacity': maskState.opacity },
          layout: { visibility: maskState.visible ? 'visible' : 'none' },
        })
      }
    }

    // 3. OIL POLYGON (Vector Geometry)
    const effectiveSpillData = spillGeometry?.geojson_polygon
      ? (spillGeometry.geojson_polygon.type === 'Feature' || spillGeometry.geojson_polygon.type === 'FeatureCollection'
          ? spillGeometry.geojson_polygon
          : {
              type: 'Feature',
              geometry: spillGeometry.geojson_polygon,
              properties: {
                area_km2: spillGeometry.area_km2,
                perimeter_km: spillGeometry.perimeter_km,
                projected_crs: spillGeometry.projected_crs,
              },
            })
      : spillPolygon

    const oilPolyState = getLayerState('oil_polygon', true, 0.75)
    if (effectiveSpillData) {
      setGeoJSONSource('spill-source', effectiveSpillData)
      if (!m.getLayer('spill-fill')) {
        m.addLayer({
          id: 'spill-fill',
          type: 'fill',
          source: 'spill-source',
          paint: {
            'fill-color': '#d97706',
            'fill-opacity': oilPolyState.opacity,
          },
          layout: { visibility: oilPolyState.visible ? 'visible' : 'none' },
        })
        m.addLayer({
          id: 'spill-stroke',
          type: 'line',
          source: 'spill-source',
          paint: {
            'line-color': '#f59e0b',
            'line-width': 2.5,
          },
          layout: { visibility: oilPolyState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('spill-fill', 'visibility', oilPolyState.visible ? 'visible' : 'none')
        m.setLayoutProperty('spill-stroke', 'visibility', oilPolyState.visible ? 'visible' : 'none')
        m.setPaintProperty('spill-fill', 'fill-opacity', oilPolyState.opacity)
      }
    }

    // 4. LOOK-ALIKE REGIONS
    const lookalikeState = getLayerState('lookalike_regions', true, 0.5)
    if (lookalikeRegions) {
      setGeoJSONSource('lookalike-source', lookalikeRegions)
      if (!m.getLayer('lookalike-fill')) {
        m.addLayer({
          id: 'lookalike-fill',
          type: 'fill',
          source: 'lookalike-source',
          paint: {
            'fill-color': [
              'match',
              ['get', 'class_name'],
              'ALGAE_LIKE', '#10b981',
              'SHIP_WAKE', '#06b6d4',
              'LOW_WIND_DARK_AREA', '#8b5cf6',
              'COASTAL_ARTIFACT', '#64748b',
              '#94a3b8',
            ],
            'fill-opacity': lookalikeState.opacity,
          },
          layout: { visibility: lookalikeState.visible ? 'visible' : 'none' },
        })
        m.addLayer({
          id: 'lookalike-stroke',
          type: 'line',
          source: 'lookalike-source',
          paint: {
            'line-color': '#64748b',
            'line-width': 1,
            'line-dasharray': [2, 2],
          },
          layout: { visibility: lookalikeState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('lookalike-fill', 'visibility', lookalikeState.visible ? 'visible' : 'none')
        m.setLayoutProperty('lookalike-stroke', 'visibility', lookalikeState.visible ? 'visible' : 'none')
        m.setPaintProperty('lookalike-fill', 'fill-opacity', lookalikeState.opacity)
      }
    }

    // 5. BACKWARD PARTICLES & TIMESTEP ANIMATION
    const particleState = getLayerState('backward_particles', true, 0.8)
    if (particleTimesteps) {
      let currentParticles = particleTimesteps
      if (particleTimesteps.type === 'FeatureCollection' && Array.isArray(particleTimesteps.features)) {
        const filtered = particleTimesteps.features.filter(
          (f: any) => f.properties?.hour_idx === currentHour || f.properties?.step === currentHour
        )
        if (filtered.length > 0) {
          currentParticles = { type: 'FeatureCollection', features: filtered }
        }
      }
      setGeoJSONSource('particles-source', currentParticles)
      if (!m.getLayer('particles-circle')) {
        m.addLayer({
          id: 'particles-circle',
          type: 'circle',
          source: 'particles-source',
          paint: {
            'circle-radius': 3.5,
            'circle-color': '#06b6d4',
            'circle-opacity': particleState.opacity,
            'circle-stroke-width': 0.5,
            'circle-stroke-color': '#ffffff',
          },
          layout: { visibility: particleState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('particles-circle', 'visibility', particleState.visible ? 'visible' : 'none')
        m.setPaintProperty('particles-circle', 'circle-opacity', particleState.opacity)
      }
    }

    // 6. ORIGIN PROBABILITY (P50, P75, P90)
    const probState = getLayerState('origin_probability', true, 0.6)
    if (originP90) {
      setGeoJSONSource('origin-p90-source', originP90)
      if (!m.getLayer('origin-p90-fill')) {
        m.addLayer({
          id: 'origin-p90-fill',
          type: 'fill',
          source: 'origin-p90-source',
          paint: { 'fill-color': '#3b82f6', 'fill-opacity': probState.opacity * 0.3 },
          layout: { visibility: probState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('origin-p90-fill', 'visibility', probState.visible ? 'visible' : 'none')
      }
    }
    if (originP75) {
      setGeoJSONSource('origin-p75-source', originP75)
      if (!m.getLayer('origin-p75-fill')) {
        m.addLayer({
          id: 'origin-p75-fill',
          type: 'fill',
          source: 'origin-p75-source',
          paint: { 'fill-color': '#6366f1', 'fill-opacity': probState.opacity * 0.5 },
          layout: { visibility: probState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('origin-p75-fill', 'visibility', probState.visible ? 'visible' : 'none')
      }
    }
    if (originP50) {
      setGeoJSONSource('origin-p50-source', originP50)
      if (!m.getLayer('origin-p50-fill')) {
        m.addLayer({
          id: 'origin-p50-fill',
          type: 'fill',
          source: 'origin-p50-source',
          paint: { 'fill-color': '#ec4899', 'fill-opacity': probState.opacity * 0.75 },
          layout: { visibility: probState.visible ? 'visible' : 'none' },
        })
        m.addLayer({
          id: 'origin-p50-stroke',
          type: 'line',
          source: 'origin-p50-source',
          paint: { 'line-color': '#f43f5e', 'line-width': 2 },
          layout: { visibility: probState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('origin-p50-fill', 'visibility', probState.visible ? 'visible' : 'none')
        m.setLayoutProperty('origin-p50-stroke', 'visibility', probState.visible ? 'visible' : 'none')
      }
    }

    // 7. ORIGIN UNCERTAINTY ENVELOPE
    const uncertState = getLayerState('origin_uncertainty', true, 0.4)
    if (originUncertaintyEnvelope) {
      setGeoJSONSource('origin-uncert-source', originUncertaintyEnvelope)
      if (!m.getLayer('origin-uncert-line')) {
        m.addLayer({
          id: 'origin-uncert-line',
          type: 'line',
          source: 'origin-uncert-source',
          paint: {
            'line-color': '#94a3b8',
            'line-width': 1.5,
            'line-dasharray': [4, 2],
          },
          layout: { visibility: uncertState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('origin-uncert-line', 'visibility', uncertState.visible ? 'visible' : 'none')
      }
    }

    // 8. AIS VESSEL POINTS
    const aisPointsState = getLayerState('ais_vessel_points', true, 0.9)
    if (aisVesselPoints) {
      setGeoJSONSource('ais-points-source', aisVesselPoints)
      if (!m.getLayer('ais-points-circle')) {
        m.addLayer({
          id: 'ais-points-circle',
          type: 'circle',
          source: 'ais-points-source',
          paint: {
            'circle-radius': 4,
            'circle-color': '#38bdf8',
            'circle-stroke-width': 1,
            'circle-stroke-color': '#0f172a',
            'circle-opacity': aisPointsState.opacity,
          },
          layout: { visibility: aisPointsState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('ais-points-circle', 'visibility', aisPointsState.visible ? 'visible' : 'none')
        m.setPaintProperty('ais-points-circle', 'circle-opacity', aisPointsState.opacity)
      }
    }

    // 9. AIS VESSEL TRACKS
    const aisTracksState = getLayerState('ais_vessel_tracks', true, 0.7)
    if (aisVesselTracks) {
      setGeoJSONSource('ais-tracks-source', aisVesselTracks)
      if (!m.getLayer('ais-tracks-line')) {
        m.addLayer({
          id: 'ais-tracks-line',
          type: 'line',
          source: 'ais-tracks-source',
          paint: {
            'line-color': '#0ea5e9',
            'line-width': 2,
            'line-opacity': aisTracksState.opacity,
          },
          layout: { visibility: aisTracksState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('ais-tracks-line', 'visibility', aisTracksState.visible ? 'visible' : 'none')
        m.setPaintProperty('ais-tracks-line', 'line-opacity', aisTracksState.opacity)
      }
    }

    // 10. CANDIDATE VESSEL TRACKS
    const candState = getLayerState('candidate_vessel_tracks', true, 0.9)
    if (candidateVessels && candidateVessels.length > 0) {
      const candFeatures = candidateVessels.map((v) => ({
        type: 'Feature',
        geometry: v.track_geometry || {
          type: 'Point',
          coordinates: [v.lon, v.lat],
        },
        properties: {
          mmsi: v.mmsi,
          vessel_name: v.vessel_name || v.mmsi,
          vessel_type: v.vessel_type || 'Unknown',
          physical_score: v.physical_score || 0,
          rank: v.rank || '-',
        },
      }))
      const candCollection = { type: 'FeatureCollection', features: candFeatures }
      setGeoJSONSource('candidate-vessels-source', candCollection)

      if (!m.getLayer('candidate-vessels-point')) {
        m.addLayer({
          id: 'candidate-vessels-point',
          type: 'circle',
          source: 'candidate-vessels-source',
          paint: {
            'circle-radius': 7,
            'circle-color': '#ef4444',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
            'circle-opacity': candState.opacity,
          },
          layout: { visibility: candState.visible ? 'visible' : 'none' },
        })

        m.on('click', 'candidate-vessels-point', (e) => {
          if (e.features && e.features[0]) {
            const props = e.features[0].properties as any
            if (onVesselSelect && props.mmsi) {
              onVesselSelect(props.mmsi)
            }
          }
        })
      } else {
        m.setLayoutProperty('candidate-vessels-point', 'visibility', candState.visible ? 'visible' : 'none')
        m.setPaintProperty('candidate-vessels-point', 'circle-opacity', candState.opacity)
      }
    }

    // 11. COUNTERFACTUAL SIMULATED SLICK
    const simState = getLayerState('counterfactual_simulated_slick', true, 0.7)
    if (counterfactualSimulatedSlick) {
      setGeoJSONSource('simulated-slick-source', counterfactualSimulatedSlick)
      if (!m.getLayer('simulated-slick-fill')) {
        m.addLayer({
          id: 'simulated-slick-fill',
          type: 'fill',
          source: 'simulated-slick-source',
          paint: {
            'fill-color': '#8b5cf6',
            'fill-opacity': simState.opacity * 0.6,
          },
          layout: { visibility: simState.visible ? 'visible' : 'none' },
        })
        m.addLayer({
          id: 'simulated-slick-stroke',
          type: 'line',
          source: 'simulated-slick-source',
          paint: {
            'line-color': '#a78bfa',
            'line-width': 2,
            'line-dasharray': [3, 2],
          },
          layout: { visibility: simState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('simulated-slick-fill', 'visibility', simState.visible ? 'visible' : 'none')
        m.setLayoutProperty('simulated-slick-stroke', 'visibility', simState.visible ? 'visible' : 'none')
        m.setPaintProperty('simulated-slick-fill', 'fill-opacity', simState.opacity * 0.6)
      }
    }

    // 12. OBSERVED VS SIMULATED COMPARISON (OVERLAP REGION)
    const compState = getLayerState('observed_vs_simulated_comparison', true, 0.8)
    if (observedVsSimulatedComparison) {
      setGeoJSONSource('comparison-overlap-source', observedVsSimulatedComparison)
      if (!m.getLayer('comparison-overlap-fill')) {
        m.addLayer({
          id: 'comparison-overlap-fill',
          type: 'fill',
          source: 'comparison-overlap-source',
          paint: {
            'fill-color': '#10b981',
            'fill-opacity': compState.opacity * 0.7,
          },
          layout: { visibility: compState.visible ? 'visible' : 'none' },
        })
        m.addLayer({
          id: 'comparison-overlap-stroke',
          type: 'line',
          source: 'comparison-overlap-source',
          paint: {
            'line-color': '#34d399',
            'line-width': 2.5,
          },
          layout: { visibility: compState.visible ? 'visible' : 'none' },
        })
      } else {
        m.setLayoutProperty('comparison-overlap-fill', 'visibility', compState.visible ? 'visible' : 'none')
        m.setLayoutProperty('comparison-overlap-stroke', 'visibility', compState.visible ? 'visible' : 'none')
        m.setPaintProperty('comparison-overlap-fill', 'fill-opacity', compState.opacity * 0.7)
      }
    }
  }, [
    mapLoaded,
    satelliteRasterUrl,
    satelliteRasterBounds,
    detectionMaskUrl,
    spillPolygon,
    spillGeometry,
    lookalikeRegions,
    hindcastTrajectories,
    particleTimesteps,
    currentHour,
    originP50,
    originP75,
    originP90,
    originUncertaintyEnvelope,
    aisVesselPoints,
    aisVesselTracks,
    candidateVessels,
    counterfactualSimulatedSlick,
    observedVsSimulatedComparison,
    layerConfigs,
  ])

  return (
    <div className="relative w-full h-full min-h-[500px] bg-slate-950">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  )
}
