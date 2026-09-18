'use client'

import React from 'react'
import Link from 'next/link'
import { AlertTriangle, Play, ArrowLeft, ShieldAlert, CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api/client'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'

export default function DemoModePage() {
  const router = useRouter()

  const handleLaunchDemo = async () => {
    try {
      // Create explicit demo incident
      const incident = await api.post<any>('/incidents', {
        title: 'DEMO CASE — Gulf of Mexico Synthetic Test Spill',
        description: 'Demonstration investigation with pre-configured synthetic SAR detection, reverse drift, and candidate vessel track.',
        operator: 'Demo Evaluator',
      })

      toast.success('Demo environment loaded')
      router.push(`/incidents/${incident.id}`)
    } catch (err: any) {
      toast.error('Failed to create demo instance')
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 py-12 px-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>

        <div className="bg-amber-950/40 border border-amber-800/80 rounded-xl p-6 flex flex-col gap-4 shadow-lg">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-amber-400 flex-shrink-0" />
            <div>
              <h1 className="text-lg font-bold text-amber-200">SlickTrace Offline Demonstration Mode</h1>
              <p className="text-xs text-amber-300/80 mt-0.5">
                Explicit demonstration environment for offline evaluation and training.
              </p>
            </div>
          </div>

          <div className="text-xs text-slate-300 leading-relaxed space-y-2 border-t border-amber-900/50 pt-3">
            <p>
              In accordance with the <strong>SlickTrace Core Product Contract</strong>:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400">
              <li>REAL MODE never silently falls back to synthetic or demo datasets.</li>
              <li>Missing external feeds (Copernicus, CDS, CMEMS) clearly surface an <code className="font-mono text-amber-300">UNAVAILABLE</code> state.</li>
              <li>DEMO MODE is strictly compartmentalized and clearly stamped on all outputs and PDF dossiers.</li>
            </ul>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleLaunchDemo}
              className="bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg flex items-center gap-2 transition-colors shadow"
            >
              <Play className="w-4 h-4" />
              <span>Launch Demo Investigation Session</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
