'use client'

import React, { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Plus,
  Search,
  RefreshCw,
  FolderSearch,
  Trash2,
  Archive,
  Copy,
  ExternalLink,
  AlertTriangle,
  Clock,
  CheckCircle2,
  FileCheck2,
  ArrowRight,
} from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Dropdown } from '@/components/ui/Dropdown'
import { Modal } from '@/components/ui/Modal'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/LoadingState'
import { api } from '@/lib/api/client'
import { Incident } from '@/lib/api/types'
import { toast } from 'sonner'

export default function IncidentsDirectoryPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  // State Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [regionFilter, setRegionFilter] = useState<string>('all')
  const [deleteTargetIncident, setDeleteTargetIncident] = useState<Incident | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Query Incidents
  const {
    data: incidents = [],
    isLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => api.get<Incident[]>('/incidents').catch(() => []),
  })

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/incidents/${id}`)
    },
    onSuccess: () => {
      toast.success('Investigation case deleted')
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
      setDeleteTargetIncident(null)
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Failed to delete investigation')
    },
    onSettled: () => {
      setIsDeleting(false)
    },
  })

  // Archive Mutation
  const archiveMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/incidents/${id}`, { status: 'closed' })
    },
    onSuccess: () => {
      toast.success('Investigation archived')
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Failed to archive investigation')
    },
  })

  // Filtered investigations list
  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        const matchTitle = inc.title?.toLowerCase().includes(q)
        const matchCaseId = inc.case_id?.toLowerCase().includes(q)
        const matchDesc = inc.description?.toLowerCase().includes(q)
        if (!matchTitle && !matchCaseId && !matchDesc) return false
      }
      if (statusFilter !== 'all' && inc.status !== statusFilter) return false
      if (regionFilter !== 'all' && inc.region !== regionFilter) return false
      return true
    })
  }, [incidents, searchQuery, statusFilter, regionFilter])

  return (
    <AppShell>
      <PageHeader
        title="Investigations Ledger"
        description="Comprehensive case directory of maritime oil-spill forensic investigations. Filter by operational status, oceanic sector, and acquisition date."
        badge={<Badge variant="real">DATABASE</Badge>}
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              leftIcon={RefreshCw}
              isLoading={isFetching}
              onClick={() => refetch()}
            >
              Refresh
            </Button>
            <Link href="/incidents/new">
              <Button variant="primary" size="sm" leftIcon={Plus}>
                New Investigation
              </Button>
            </Link>
          </div>
        }
      />

      {/* Filter Bar */}
      <Card variant="default">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              placeholder="Search Case ID, title, or AOI coordinates..."
              leftIcon={Search}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Dropdown
              options={[
                { value: 'all', label: 'All Statuses' },
                { value: 'open', label: 'Open' },
                { value: 'in_progress', label: 'In Progress' },
                { value: 'closed', label: 'Closed / Archived' },
              ]}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            />
            <Dropdown
              options={[
                { value: 'all', label: 'All Oceanic Sectors' },
                { value: 'Persian Gulf', label: 'Persian Gulf / Strait of Hormuz' },
                { value: 'Gulf of Mexico', label: 'Gulf of Mexico' },
                { value: 'North Sea', label: 'North Sea' },
                { value: 'Singapore Strait', label: 'Singapore Strait / Malacca' },
                { value: 'Mediterranean', label: 'Mediterranean Sea' },
              ]}
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Main Investigations Table */}
      <Card variant="default">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <FolderSearch className="w-4 h-4 text-sky-400" />
              <span>Registered Incident Cases</span>
            </CardTitle>
            <CardDescription>
              {filteredIncidents.length} of {incidents.length} investigations matching filter criteria
            </CardDescription>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {incidents.length} Total
          </span>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <TableSkeleton rows={4} cols={6} />
          ) : filteredIncidents.length === 0 ? (
            <EmptyState
              icon={FolderSearch}
              title={incidents.length === 0 ? 'No investigations found' : 'No matching cases'}
              description={
                incidents.length === 0
                  ? 'Create your first investigation to begin satellite-to-vessel analysis. Real mode starts with zero pre-seeded incidents.'
                  : 'No investigations matched your active search or filter criteria. Adjust your filters or create a new case.'
              }
              actionLabel="Create Investigation"
              actionIcon={Plus}
              onAction={() => router.push('/incidents/new')}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Case ID</TableHead>
                  <TableHead>Investigation Title</TableHead>
                  <TableHead>Oceanic Region</TableHead>
                  <TableHead>Date (UTC)</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredIncidents.map((inc) => (
                  <TableRow key={inc.id}>
                    <TableCell className="font-mono font-bold text-sky-400">
                      {inc.case_id || 'ST-REAL'}
                    </TableCell>
                    <TableCell className="font-medium text-slate-100 max-w-xs truncate">
                      {inc.title}
                    </TableCell>
                    <TableCell className="font-mono text-slate-400 text-xs">
                      {inc.region || 'Global'}
                    </TableCell>
                    <TableCell className="font-mono text-slate-400 text-xs">
                      {inc.incident_time_utc
                        ? new Date(inc.incident_time_utc).toISOString().slice(0, 10)
                        : 'UNSET'}
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
                      <div className="flex items-center justify-end space-x-1.5">
                        <Link href={`/incidents/${inc.id}`}>
                          <Button variant="primary" size="sm" rightIcon={ArrowRight}>
                            Open
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Archive Investigation"
                          onClick={() => archiveMutation.mutate(inc.id)}
                        >
                          <Archive className="w-3.5 h-3.5 text-slate-400 hover:text-amber-400" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Delete Case"
                          onClick={() => setDeleteTargetIncident(inc)}
                        >
                          <Trash2 className="w-3.5 h-3.5 text-slate-400 hover:text-rose-400" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(deleteTargetIncident)}
        onClose={() => setDeleteTargetIncident(null)}
        title="Confirm Permanent Deletion"
        description="This action will delete all satellite evidence, OpenDrift simulation runs, and candidate attribution tables for this case."
        maxWidth="md"
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300 font-mono">
            Target Case: {deleteTargetIncident?.title} ({deleteTargetIncident?.case_id || 'ST-CASE'})
          </div>
          <p className="text-xs text-slate-300">
            Are you sure you want to permanently delete this investigation? This action cannot be undone.
          </p>
          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setDeleteTargetIncident(null)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={isDeleting}
              onClick={() => {
                if (deleteTargetIncident) {
                  setIsDeleting(true)
                  deleteMutation.mutate(deleteTargetIncident.id)
                }
              }}
            >
              Delete Case Permanently
            </Button>
          </div>
        </div>
      </Modal>
    </AppShell>
  )
}
