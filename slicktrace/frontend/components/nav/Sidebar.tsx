'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Waves,
  Satellite,
  Ship,
  Database,
  Activity,
  FileText,
  HeartPulse,
  Plus,
  Shield,
  ChevronRight,
  LogOut,
  Sliders,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSlickTraceStore } from '@/lib/stores/slicktrace'

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useSlickTraceStore()

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/incidents', label: 'Investigations', icon: Waves },
    { href: '/satellite', label: 'Satellite Ingestion', icon: Satellite },
    { href: '/vessels', label: 'AIS Fleet Search', icon: Ship },
    { href: '/datasets', label: 'Dataset Vault', icon: Database },
    { href: '/analysis-runs', label: 'Analysis Runs', icon: Activity },
    { href: '/reports', label: 'Forensic Reports', icon: FileText },
    { href: '/system-health', label: 'System Health', icon: HeartPulse },
  ]

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0 h-screen sticky top-0 z-30 select-none font-sans">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-ocean-600 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-ocean-900/40 group-hover:scale-105 transition-transform">
            <Waves className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
              <span>SlickTrace</span>
              <span className="text-[10px] font-mono font-extrabold px-1.5 py-0.2 rounded bg-ocean-950 text-ocean-300 border border-ocean-800">
                v2.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400">Maritime Forensics</p>
          </div>
        </Link>
      </div>

      {/* New Investigation Quick Action */}
      <div className="p-3 border-b border-slate-800/80">
        <Link
          href="/incidents/new"
          className="w-full btn-primary py-2 px-3 text-xs flex items-center justify-center gap-2 shadow-md shadow-brand-900/30"
        >
          <Plus className="w-4 h-4" />
          <span>New Investigation</span>
        </Link>
      </div>

      {/* Main Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-2 pb-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-300">
          Core Workflows
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive =
            pathname === item.href ||
            (item.href !== '/dashboard' && pathname.startsWith(item.href))

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all group',
                isActive
                  ? 'bg-ocean-600/90 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/70'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={cn(
                    'w-4 h-4 transition-colors',
                    isActive ? 'text-white' : 'text-slate-400 group-hover:text-ocean-400'
                  )}
                />
                <span>{item.label}</span>
              </div>
              {isActive && <ChevronRight className="w-3.5 h-3.5 text-white/80" />}
            </Link>
          )
        })}
      </nav>

      {/* Footer / Status */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex flex-col gap-2 text-xs">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-mono text-slate-300">Engine Online</span>
          </div>
          <Link
            href="/settings"
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            title="Settings"
          >
            <Sliders className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[11px] text-slate-400">
          <div className="truncate max-w-[130px]" title={user?.email || 'investigator@agency.gov'}>
            <span className="text-slate-300 font-medium">{user?.role || 'Investigator'}</span>
          </div>
          <Link
            href="/login"
            onClick={() => logout()}
            className="text-slate-400 hover:text-danger-400 flex items-center gap-1 text-[10px]"
            title="Sign Out"
          >
            <LogOut className="w-3 h-3" />
            <span>Switch</span>
          </Link>
        </div>
      </div>
    </aside>
  )
}
