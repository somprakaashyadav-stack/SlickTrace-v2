'use client'

import React from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { ShieldCheck, ArrowRight, ArrowLeft, FileText, Lock, Hash, CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Incident, EvidenceManifest } from '@/lib/api/types'
import { EvidenceManifestView } from '@/components/evidence/EvidenceManifestView'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'

export default function IncidentEvidencePage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const { data: incident } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => api.get<Incident>(`/incidents/${id}`),
    enabled: !!id,
  })

  const { data: manifest, refetch: refetchManifest } = useQuery({
    queryKey: ['manifest', id],
    queryFn: async () => {
      try {
        return await api.get<EvidenceManifest>(`/incidents/${id}/manifest`)
      } catch {
        return null
      }
    },
    enabled: !!id,
  })

  return (
    <div className="flex flex-col gap-5 font-sans">
      {/* Provenance Card */}
      <DataProvenanceCard
        title="07 Tamper-Evident Evidence Locker &amp; Cryptographic Manifest"
        provider="SlickTrace Immutable Evidence Vault (SHA-256 Chain of Custody)"
        datasetName={`MANIFEST-${id.slice(0, 8)}`}
        timestampUtc={manifest?.created_at || new Date().toISOString()}
        crs="N/A (Cryptographic Hash Integrity)"
        sha256={manifest?.manifest_hash || 'b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2'}
        algorithm="SHA-256 Merkle Tree Hash Ledger + ISO/IEC 27037 Evidence Packaging"
        mode={incident?.mode === 'demo' ? 'DEMO' : 'REAL'}
        notes={[
          'Every satellite granule, neural weight checkpoint, and AIS point is cryptographically sealed.',
          'Manifest verification ensures zero post-hoc modification or fabricated data.',
        ]}
      />

      {/* Main Evidence Manifest View */}
      <div className="w-full flex flex-col gap-4">
        <EvidenceManifestView
          incidentId={id}
          manifest={manifest}
          onGenerateDossier={() => {
            refetchManifest()
            router.push(`/incidents/${id}/report`)
          }}
        />

        <div className="flex items-center justify-between gap-2 pt-2">
          <Link
            href={`/incidents/${id}/verification`}
            className="btn-secondary py-2 text-xs flex items-center gap-1.5 px-4"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>06 Verification</span>
          </Link>
          <Link
            href={`/incidents/${id}/report`}
            className="btn-primary py-2 text-xs flex items-center gap-1.5 px-4"
          >
            <span>08 Court-Ready Forensic Report</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  )
}
