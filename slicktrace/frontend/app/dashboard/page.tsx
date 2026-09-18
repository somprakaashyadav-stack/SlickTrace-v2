'use client'

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  Plus,
  RefreshCw,
  Clock,
  Search,
  AlertTriangle,
  CheckCircle2,
  FolderSearch,
  Ship,
  Wind,
  Database,
  ShieldCheck,
  Play,
  ArrowRight,
  Layers,
  Activity,
  Server,
  FileText,
} from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusIndicator } from '@/components/ui/StatusIndicator'
import { CardSkeleton, TableSkeleton } from '@/components/ui/LoadingState'
import { MapContainer } from '@/components/map/MapContainer'
import { api } from '@/lib/api/client'
import { Incident } from '@/lib/api/types'
import { formatDistanceToNow } from 'date-fns'

interface HealthServicesResponse {
  mode: string
  services: Record<
    string,
    {
      name: string
      status: string
      ok: boolean
    }
  >
}

export default function DashboardPage() {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null)

  // 1. Fetch Investigations from Database
  const {
    data: incidents = [],
    isLoading: incidentsLoading,
    refetch: refetchIncidents,
    isFetching,
  } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => api.get<Incident[]>('/incidents').catch(() => []),
    refetchInterval: 15000,
  })

  // 2. Fetch Live Health & Provider Statuses from Backend /health/services
  const { data: healthResponse } = useQuery<HealthServicesResponse>({
    queryKey: ['health-services'],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const baseUrl = apiUrl.replace('/api/v1', '')
      const res = await fetch(`${baseUrl}/health/services`)
      return res.json()
    },
    refetchInterval: 30000,
  })

  const services = healthResponse?.services || {}

  const activeIncident = selectedIncidentId
    ? incidents.find((i) => i.id === selectedIncidentId)
    : incidents.length > 0
    ? incidents[0]
    : null

  return (
    <AppShell>
      <PageHeader
        title="Executive Operations Dashboard"
        description="Real-time situational awareness across satellite SAR detections, ocean-physics backward hindcasts, historical AIS candidate attribution, and cryptographic evidence packages."
        badge={<Badge variant="real">COMMAND CENTER</Badge>}
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              leftIcon={RefreshCw}
              isLoading={isFetching}
              onClick={() => refetchIncidents()}
            >
              Sync Telemetry
            </Button>
            <Link href="/incidents/new">
              <Button variant="primary" size="sm" leftIcon={Plus}>
                New Investigation
              </Button>
            </Link>
          </div>
        }
      />

      {/* 7 KPI Operational Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        {/* KPI 1: Active Cases */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">Active Cases</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xl font-bold font-mono text-sky-400">{incidents.length}</div>
            <p className="text-[10px] text-slate-400">Registered incidents</p>
          </CardContent>
        </Card>

        {/* KPI 2: Running Jobs */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">Running Jobs</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xl font-bold font-mono text-slate-100">0</div>
            <p className="text-[10px] text-slate-400">Async tasks</p>
          </CardContent>
        </Card>

        {/* KPI 3: Satellite CDSE */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">Satellite SAR</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xs font-bold font-mono text-amber-400 truncate">
              {services.satellite_provider?.status || 'NOT CONFIGURED'}
            </div>
            <p className="text-[10px] text-slate-400">Copernicus CDSE</p>
          </CardContent>
        </Card>

        {/* KPI 4: AIS Provider */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">AIS Provider</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xs font-bold font-mono text-emerald-400 truncate">
              {services.ais_provider?.status || 'LOCAL ENGINE (DuckDB)'}
            </div>
            <p className="text-[10px] text-slate-400">MarineCadastre</p>
          </CardContent>
        </Card>

        {/* KPI 5: Metocean */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">Metocean</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xs font-bold font-mono text-amber-400 truncate">
              {services.metocean_provider?.status || 'NOT CONFIGURED'}
            </div>
            <p className="text-[10px] text-slate-400">ERA5 / CMEMS</p>
          </CardContent>
        </Card>

        {/* KPI 6: Evidence Packs */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">Evidence Packs</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xl font-bold font-mono text-cyan-400">0</div>
            <p className="text-[10px] text-slate-400">Sealed SHA-256</p>
          </CardContent>
        </Card>

        {/* KPI 7: Ocean Engine */}
        <Card variant="default">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[11px] font-mono text-slate-400">Lagrangian Drift</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="text-xs font-bold font-mono text-sky-400 truncate">
              {services.opendrift?.status || 'STANDBY'}
            </div>
            <p className="text-[10px] text-slate-400">OpenDrift Physics</p>
          </CardContent>
        </Card>
      </div>

      {/* Tactical GIS Map Canvas */}
      <Card variant="default">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <span>Tactical GIS Spatiotemporal Canvas</span>
            </CardTitle>
            <CardDescription>
              {activeIncident
                ? `Active Investigation: ${activeIncident.title} (${activeIncident.case_id || 'ST-ACTIVE'})`
                : 'No active investigation geometry selected. Select or create an investigation to render SAR scenes and particle trajectories.'}
            </CardDescription>
          </div>
          {activeIncident && (
            <Link href={`/incidents/${activeIncident.id}`}>
              <Button variant="outline" size="sm" rightIcon={ArrowRight}>
                Open Case Workspace
              </Button>
            </Link>
          )}
        </CardHeader>
        <CardContent className="p-0">
          <MapContainer
            hasGeometry={Boolean(activeIncident)}
            emptyMessage="No active investigation geometry available. Create an investigation to begin satellite-to-vessel analysis."
          />
        </CardContent>
      </Card>

      {/* Two-Column Operations Ledger */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Investigations Table */}
        <div className="lg:col-span-2">
          <Card variant="default" className="h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <FolderSearch className="w-4 h-4 text-sky-400" />
                  <span>Recent Investigations</span>
                </CardTitle>
                <CardDescription>Database ledger of registered oil-spill incidents</CardDescription>
              </div>
              <Link href="/incidents">
                <Button variant="ghost" size="sm" rightIcon={ArrowRight}>
                  View All
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {incidentsLoading ? (
                <TableSkeleton rows={3} cols={5} />
              ) : incidents.length === 0 ? (
                <EmptyState
                  icon={FolderSearch}
                  title="No investigations found"
                  description="Create your first investigation in REAL MODE to begin satellite SAR ingestion, backward hindcast, and AIS candidate vessel ranking."
                  actionLabel="Create Investigation"
                  actionIcon={Plus}
                  onAction={() => window.location.assign('/incidents/new')}
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Case ID</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Region</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {incidents.slice(0, 5).map((inc) => (
                      <TableRow
                        key={inc.id}
                        className={selectedIncidentId === inc.id ? 'bg-sky-950/40' : ''}
                      >
                        <TableCell className="font-mono font-bold text-sky-300">
                          {inc.case_id || 'ST-REAL'}
                        </TableCell>
                        <TableCell className="font-medium text-slate-100">{inc.title}</TableCell>
                        <TableCell className="text-slate-400 font-mono text-[11px]">
                          {inc.region || 'Global Waters'}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              inc.status === 'closed'
                                ? 'success'
                                : inc.status === 'in_progress'
                                ? 'warning'
                                : 'info'
                            }
                          >
                            {inc.status || 'OPEN'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Link href={`/incidents/${inc.id}`}>
                            <Button variant="ghost" size="sm" rightIcon={ArrowRight}>
                              Inspect
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Col: Live Subsystem Stream */}
        <div>
          <Card variant="default" className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Subsystem Health Stream</span>
              </CardTitle>
              <CardDescription>Live diagnostics from backend providers</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(services).length === 0 ? (
                <div className="p-4 text-center text-xs font-mono text-slate-400">
                  <StatusIndicator status="standby" label="Connecting to health API..." />
                </div>
              ) : (
                Object.entries(services).map(([key, s]) => (
                  <div
                    key={key}
                    className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{s.name}</div>
                      <div className="text-[10px] font-mono text-slate-400 truncate max-w-[170px]">
                        {s.status}
                      </div>
                    </div>
                    <Badge variant={s.ok ? 'success' : 'neutral'} size="sm">
                      {s.ok ? 'ONLINE' : 'STANDBY'}
                    </Badge>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  )
}
