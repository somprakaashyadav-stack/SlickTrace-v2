/**
 * SlickTrace v2 — Zustand Global Store
 */
import { create } from 'zustand'
import { Incident, SpillDetection, HindcastRun, CandidateVessel, AuthUser } from '@/lib/api/types'

interface PipelineProgress {
  detection?: { status: string; message?: string }
  hindcast?: { status: string; message?: string }
  ais?: { status: string; message?: string }
  scoring?: { status: string; message?: string }
  dossier?: { status: string; message?: string }
}

interface SlickTraceStore {
  // Auth state
  user: AuthUser | null
  setUser: (user: AuthUser | null) => void
  token: string | null
  setToken: (token: string | null) => void
  logout: () => void

  // Mode: 'real' | 'demo'
  appMode: 'real' | 'demo'
  setAppMode: (mode: 'real' | 'demo') => void

  // Active incident
  activeIncident: Incident | null
  setActiveIncident: (incident: Incident | null) => void

  // Pipeline progress (from WebSocket)
  pipelineProgress: PipelineProgress
  updateProgress: (stage: keyof PipelineProgress, data: { status: string; message?: string }) => void

  // Selected detection / hindcast for map display
  selectedDetectionId: string | null
  setSelectedDetectionId: (id: string | null) => void

  selectedHindcastId: string | null
  setSelectedHindcastId: (id: string | null) => void

  selectedCandidateMMSI: string | null
  setSelectedCandidateMMSI: (mmsi: string | null) => void

  // Map viewport
  mapViewport: { latitude: number; longitude: number; zoom: number }
  setMapViewport: (viewport: { latitude: number; longitude: number; zoom: number }) => void
}

export const useSlickTraceStore = create<SlickTraceStore>((set) => ({
  user: null,
  setUser: (user) => set({ user, appMode: user?.mode || 'real' }),
  token: null,
  setToken: (token) => set({ token }),
  logout: () =>
    set({
      user: null,
      token: null,
      activeIncident: null,
      appMode: 'real',
    }),

  appMode: 'real',
  setAppMode: (appMode) => set({ appMode }),

  activeIncident: null,
  setActiveIncident: (incident) => set({ activeIncident: incident }),

  pipelineProgress: {},
  updateProgress: (stage, data) =>
    set((state) => ({
      pipelineProgress: { ...state.pipelineProgress, [stage]: data },
    })),

  selectedDetectionId: null,
  setSelectedDetectionId: (id) => set({ selectedDetectionId: id }),

  selectedHindcastId: null,
  setSelectedHindcastId: (id) => set({ selectedHindcastId: id }),

  selectedCandidateMMSI: null,
  setSelectedCandidateMMSI: (mmsi) => set({ selectedCandidateMMSI: mmsi }),

  mapViewport: { latitude: 20, longitude: 65, zoom: 4 },
  setMapViewport: (viewport) => set({ mapViewport: viewport }),
}))
