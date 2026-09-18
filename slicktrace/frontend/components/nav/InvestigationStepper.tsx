'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FileSearch,
  Waves,
  Wind,
  Ship,
  Activity,
  CheckCheck,
  ShieldCheck,
  FileText,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface StepperStep {
  num: string
  key: string
  label: string
  hrefSuffix: string
  icon: React.ElementType
}

export const INVESTIGATION_STEPS: StepperStep[] = [
  { num: '01', key: 'overview', label: 'Evidence Intake', hrefSuffix: '/overview', icon: FileSearch },
  { num: '02', key: 'detection', label: 'Detection', hrefSuffix: '/detection', icon: Waves },
  { num: '03', key: 'drift', label: 'Ocean Drift', hrefSuffix: '/drift', icon: Wind },
  { num: '04', key: 'vessels', label: 'AIS Candidates', hrefSuffix: '/vessels', icon: Ship },
  { num: '05', key: 'behavior', label: 'Behavior Analysis', hrefSuffix: '/behavior', icon: Activity },
  { num: '06', key: 'verification', label: 'Verification', hrefSuffix: '/verification', icon: CheckCheck },
  { num: '07', key: 'evidence', label: 'Evidence Locker', hrefSuffix: '/evidence', icon: ShieldCheck },
  { num: '08', key: 'report', label: 'Forensic Report', hrefSuffix: '/report', icon: FileText },
]

interface InvestigationStepperProps {
  incidentId: string
  currentStatus?: string
  className?: string
}

export function InvestigationStepper({ incidentId, currentStatus, className }: InvestigationStepperProps) {
  const pathname = usePathname()

  return (
    <div className={cn('bg-slate-900/95 border border-slate-800 rounded-2xl p-2.5 shadow-xl font-sans', className)}>
      <div className="flex items-center justify-between overflow-x-auto gap-1">
        {INVESTIGATION_STEPS.map((step, idx) => {
          const Icon = step.icon
          const targetHref = `/incidents/${incidentId}${step.hrefSuffix}`
          const isCurrent =
            pathname === targetHref ||
            (step.key === 'overview' && pathname === `/incidents/${incidentId}`)

          return (
            <React.Fragment key={step.key}>
              <Link
                href={targetHref}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all flex-shrink-0 group',
                  isCurrent
                    ? 'bg-ocean-600 text-white shadow-lg shadow-ocean-900/50 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80'
                )}
              >
                <span
                  className={cn(
                    'font-mono text-[10px] font-extrabold px-1.5 py-0.5 rounded transition-colors',
                    isCurrent
                      ? 'bg-ocean-950 text-ocean-200 border border-ocean-400/40'
                      : 'bg-slate-800 text-slate-400 group-hover:text-slate-300'
                  )}
                >
                  {step.num}
                </span>

                <Icon
                  className={cn(
                    'w-3.5 h-3.5 transition-colors',
                    isCurrent ? 'text-white' : 'text-slate-400 group-hover:text-ocean-400'
                  )}
                />

                <span>{step.label}</span>
              </Link>

              {idx < INVESTIGATION_STEPS.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-slate-700 flex-shrink-0" />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
