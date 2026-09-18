'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  FolderSearch,
  PlusCircle,
  Database,
  Activity,
  Layers,
  Wind,
  Ship,
  FileCheck2,
  FileText,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Server,
} from 'lucide-react'
import { useSlickTraceStore } from '@/lib/stores/slicktrace'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
  section?: string
}

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { activeIncident } = useSlickTraceStore()

  const mainNav: NavItem[] = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Investigations', href: '/incidents', icon: FolderSearch },
    { name: 'New Investigation', href: '/incidents/new', icon: PlusCircle },
    { name: 'Dataset Vault', href: '/datasets', icon: Database },
    { name: 'System Diagnostics', href: '/settings', icon: Activity },
  ]

  const investigationNav: NavItem[] = activeIncident
    ? [
        {
          name: 'Detection & SAR',
          href: `/incidents/${activeIncident.id}/detection`,
          icon: Layers,
        },
        {
          name: 'Drift Hindcast',
          href: `/incidents/${activeIncident.id}/drift`,
          icon: Wind,
        },
        {
          name: 'Vessel Attribution',
          href: `/incidents/${activeIncident.id}/candidates`,
          icon: Ship,
        },
        {
          name: 'Physical Consistency',
          href: `/incidents/${activeIncident.id}/physics`,
          icon: FileCheck2,
        },
        {
          name: 'Evidence Dossier',
          href: `/incidents/${activeIncident.id}/evidence`,
          icon: FileText,
        },
      ]
    : []

  const isActive = (href: string) => {
    if (href === '/dashboard' && pathname === '/dashboard') return true
    if (href !== '/dashboard' && pathname?.startsWith(href)) return true
    return false
  }

  return (
    <aside
      className={`${
        isCollapsed ? 'w-16' : 'w-64'
      } bg-slate-950/90 border-r border-slate-800/80 flex flex-col justify-between shrink-0 transition-all duration-200 select-none z-30`}
    >
      <div className="p-3 space-y-6">
        {/* Collapse Toggle */}
        <div className="flex items-center justify-between px-2">
          {!isCollapsed && (
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Operations Center
            </span>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-colors ml-auto"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-3.5 h-3.5" />
            ) : (
              <ChevronLeft className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        {/* Main Navigation */}
        <div className="space-y-1">
          {mainNav.map((item) => {
            const active = isActive(item.href)
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 ${
                  active
                    ? 'bg-sky-950/80 text-sky-300 border border-sky-500/40 shadow-sm shadow-sky-950/60 font-semibold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/80 border border-transparent'
                }`}
                title={isCollapsed ? item.name : undefined}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    active ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                {!isCollapsed && <span className="truncate">{item.name}</span>}
              </Link>
            )
          })}
        </div>

        {/* Active Investigation Context Pipeline */}
        {investigationNav.length > 0 && (
          <div className="space-y-1 pt-4 border-t border-slate-800/80">
            {!isCollapsed && (
              <div className="px-3 pb-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-sky-400 font-semibold flex items-center space-x-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                  <span className="truncate">Active Case Pipeline</span>
                </span>
              </div>
            )}
            {investigationNav.map((item) => {
              const active = isActive(item.href)
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 ${
                    active
                      ? 'bg-sky-950/80 text-sky-300 border border-sky-500/40 font-semibold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/80 border border-transparent'
                  }`}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      active ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  {!isCollapsed && <span className="truncate">{item.name}</span>}
                </Link>
              )
            })}
          </div>
        )}
      </div>

      {/* Footer System Status Card */}
      {!isCollapsed && (
        <div className="p-3 border-t border-slate-800/80">
          <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-400">Core Engine</span>
              <span className="text-emerald-400 flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Ready</span>
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between">
              <span>DuckDB Spatial</span>
              <span className="text-slate-300">v0.10</span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between">
              <span>OpenDrift</span>
              <span className="text-slate-300">Standby</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
