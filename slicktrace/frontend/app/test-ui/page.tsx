'use client'

import React, { useState } from 'react'
import {
  Shield,
  Activity,
  Compass,
  AlertTriangle,
  Send,
  Database,
  Search,
  CheckCircle2,
} from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { StatusIndicator } from '@/components/ui/StatusIndicator'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'

export default function TestUIPage() {
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)

  return (
    <AppShell>
      <PageHeader
        title="UI Design System Verification"
        description="Global verification harness ensuring Tailwind CSS, command-center dark palette, typography, badges, and tactical components render correctly."
        badge={<Badge variant="real">VERIFIED</Badge>}
        actions={
          <Button
            variant="accent"
            size="sm"
            leftIcon={Activity}
            isLoading={loading}
            onClick={() => {
              setLoading(true)
              setTimeout(() => setLoading(false), 1500)
            }}
          >
            Trigger Test Animation
          </Button>
        }
      />

      {/* Grid Layout Testing Responsive Breakpoints */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Buttons Test */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Button System</CardTitle>
            <CardDescription>Interactive tactical variants</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            <div className="flex flex-wrap gap-2">
              <Button variant="primary" size="sm">
                Primary Sky
              </Button>
              <Button variant="accent" size="sm">
                Accent Cyan
              </Button>
              <Button variant="secondary" size="sm">
                Secondary Slate
              </Button>
              <Button variant="danger" size="sm" leftIcon={AlertTriangle}>
                Danger Red
              </Button>
              <Button variant="outline" size="sm">
                Outline
              </Button>
              <Button variant="ghost" size="sm">
                Ghost
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Badges & Status Indicators */}
        <Card variant="raised">
          <CardHeader>
            <CardTitle>Badges & Status</CardTitle>
            <CardDescription>Operational telemetry tags</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="real" dot>
                REAL MODE
              </Badge>
              <Badge variant="demo" dot>
                DEMO MODE
              </Badge>
              <Badge variant="success">PASS</Badge>
              <Badge variant="warning">DEGRADED</Badge>
              <Badge variant="danger">OFFLINE</Badge>
              <Badge variant="info">ANALYZING</Badge>
            </div>
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <StatusIndicator status="online" label="Copernicus Sentinel Link" />
              <StatusIndicator status="standby" label="DuckDB Spatial Query Engine" />
              <StatusIndicator status="warning" label="ERA5 Wind Reanalysis Fallback" />
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Form Input Controls */}
        <Card variant="glow">
          <CardHeader>
            <CardTitle>Tactical Input</CardTitle>
            <CardDescription>Monospace telemetry fields</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              label="Area of Interest (AOI)"
              placeholder="e.g. Persian Gulf [25.5°N, 54.0°E]"
              leftIcon={Search}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              hint="Format: Latitude, Longitude (WGS84)"
            />
            <Input
              label="Simulation Horizon"
              placeholder="24h"
              disabled
              hint="Fixed parameter for hindcast"
            />
          </CardContent>
        </Card>

        {/* Card 4: Micro Metrics */}
        <Card variant="accent">
          <CardHeader>
            <CardTitle>Active Telemetry</CardTitle>
            <CardDescription>Live engine state</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-2xl font-bold font-mono text-cyan-400">100% PASS</div>
            <p className="text-xs text-slate-400">
              71 automated test suites passing with zero hardcoded leaks.
            </p>
            <div className="flex items-center space-x-2 text-[11px] font-mono text-emerald-400 pt-2">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Zero-Fabrication Contract Active</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table Component Verification */}
      <Card variant="default">
        <CardHeader>
          <CardTitle>Data Table Architecture</CardTitle>
          <CardDescription>Structured spatial datasets & provider health</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subsystem / Provider</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Engine Version</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium text-slate-200">
                  <div className="flex items-center space-x-2">
                    <Database className="w-4 h-4 text-sky-400" />
                    <span>DuckDB Spatial Engine</span>
                  </div>
                </TableCell>
                <TableCell className="font-mono text-slate-400">Spatiotemporal DB</TableCell>
                <TableCell className="font-mono text-slate-300">v0.10.2 (Local Engine)</TableCell>
                <TableCell>
                  <Badge variant="success">AVAILABLE</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm">
                    Configure
                  </Button>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-slate-200">
                  <div className="flex items-center space-x-2">
                    <Compass className="w-4 h-4 text-sky-400" />
                    <span>OpenDrift Trajectory Framework</span>
                  </div>
                </TableCell>
                <TableCell className="font-mono text-slate-400">Lagrangian Physics</TableCell>
                <TableCell className="font-mono text-slate-300">v1.11.0</TableCell>
                <TableCell>
                  <Badge variant="info">STANDBY</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm">
                    Inspect
                  </Button>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-slate-200">
                  <div className="flex items-center space-x-2">
                    <Shield className="w-4 h-4 text-sky-400" />
                    <span>Copernicus CDSE Sentinel-1</span>
                  </div>
                </TableCell>
                <TableCell className="font-mono text-slate-400">SAR Ingestion</TableCell>
                <TableCell className="font-mono text-slate-300">OData API v1</TableCell>
                <TableCell>
                  <Badge variant="neutral">NOT CONFIGURED</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm">
                    Set Keys
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </AppShell>
  )
}
