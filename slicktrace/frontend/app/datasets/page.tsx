'use client'

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Database,
  HardDrive,
  RefreshCw,
  UploadCloud,
  FileSpreadsheet,
  Layers,
  Clock,
  CheckCircle2,
  FolderOpen,
} from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/LoadingState'
import { api } from '@/lib/api/client'

interface DatasetRecord {
  name: string
  category: string
  format: string
  records: string
  size: string
  crs: string
  last_updated: number | string
  status: 'INDEXED' | 'READY' | 'PROCESSING' | 'ERROR' | 'NOT CONFIGURED'
}

export default function DatasetVaultPage() {
  const { data: datasets = [], isLoading, refetch, isFetching } = useQuery<DatasetRecord[]>({
    queryKey: ['dataset-vault'],
    queryFn: async () => {
      try {
        const res = await api.get<DatasetRecord[]>('/datasets')
        return res || []
      } catch (e) {
        return []
      }
    },
  })

  // Compute live summary statistics
  const mountedCount = datasets.length
  const totalRecords = mountedCount > 0 ? `${mountedCount} cataloged repositories` : '0 records'
  const storageUsed = mountedCount > 0 ? datasets.map(d => d.size).join(' + ') : '0 MB'

  return (
    <AppShell>
      <PageHeader
        title="Dataset Vault"
        description="Spatial Data Repository & DuckDB Spatial Analytics Lake. Manages historical AIS broadcasts, environmental NetCDF forcing, and georeferenced SAR imagery."
        badge={<Badge variant="real">SPATIAL LAKE</Badge>}
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              leftIcon={RefreshCw}
              isLoading={isFetching}
              onClick={() => refetch()}
            >
              Refresh Lake
            </Button>
            <Button
              variant="primary"
              size="sm"
              leftIcon={UploadCloud}
              onClick={() => alert('Dataset ingestion wizard: Drop NetCDF, Parquet, or GeoTIFF archives directly into data/ directories for automatic mounting.')}
            >
              Mount Dataset
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="default">
          <CardHeader>
            <CardTitle className="text-xs font-mono text-slate-400">Mounted Datasets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold font-mono text-sky-400">{mountedCount}</div>
            <p className="text-[11px] text-slate-400 mt-1">Active spatial tables</p>
          </CardContent>
        </Card>

        <Card variant="default">
          <CardHeader>
            <CardTitle className="text-xs font-mono text-slate-400">Spatial Engine</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold font-mono text-emerald-400">DuckDB 0.10</div>
            <p className="text-[11px] text-slate-400 mt-1">Parquet columnar acceleration</p>
          </CardContent>
        </Card>

        <Card variant="default">
          <CardHeader>
            <CardTitle className="text-xs font-mono text-slate-400">Coordinate Systems</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold font-mono text-slate-100">EPSG:4326</div>
            <p className="text-[11px] text-slate-400 mt-1">WGS84 ellipsoidal CRS</p>
          </CardContent>
        </Card>

        <Card variant="default">
          <CardHeader>
            <CardTitle className="text-xs font-mono text-slate-400">Data Integrity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold font-mono text-cyan-400">SHA-256</div>
            <p className="text-[11px] text-slate-400 mt-1">Cryptographic tamper-evident</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Datasets Table */}
      <Card variant="default">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-sky-400" />
              <span>Cataloged Spatial Repositories</span>
            </CardTitle>
            <CardDescription>
              Local disk &amp; S3 object storage mounted volumes
            </CardDescription>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {mountedCount} mounted
          </span>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <TableSkeleton rows={4} cols={8} />
          ) : datasets.length === 0 ? (
            <EmptyState
              icon={FolderOpen}
              title="No datasets mounted"
              description="No local AIS parquet tables, NetCDF hydrodynamic grids, or Sentinel COG files were found in the data/ directory. Mount datasets to enable offline analysis."
              actionLabel="Mount Spatial Data"
              actionIcon={UploadCloud}
              onAction={() => refetch()}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Dataset</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Records</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>CRS</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datasets.map((d, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-semibold font-mono text-slate-100">
                      {d.name}
                    </TableCell>
                    <TableCell className="text-sky-300">{d.category}</TableCell>
                    <TableCell className="font-mono text-slate-400">{d.format}</TableCell>
                    <TableCell className="font-mono text-slate-300">{d.records}</TableCell>
                    <TableCell className="font-mono text-slate-300">{d.size}</TableCell>
                    <TableCell className="font-mono text-slate-400">{d.crs}</TableCell>
                    <TableCell className="font-mono text-slate-400 text-[11px]">
                      {typeof d.last_updated === 'number'
                        ? new Date(d.last_updated * 1000).toISOString().slice(0, 16).replace('T', ' ') + ' UTC'
                        : d.last_updated}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge
                        variant={
                          d.status === 'READY' || d.status === 'INDEXED'
                            ? 'success'
                            : d.status === 'PROCESSING'
                            ? 'info'
                            : d.status === 'ERROR'
                            ? 'danger'
                            : 'neutral'
                        }
                      >
                        {d.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </AppShell>
  )
}
