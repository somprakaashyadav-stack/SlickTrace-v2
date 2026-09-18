'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Search,
  RefreshCw,
  LogOut,
  Sliders,
  ShieldCheck,
  User,
  Radio,
  Clock,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSlickTraceStore } from '@/lib/stores/slicktrace'

interface HeaderProps {
  title?: string
  subtitle?: string
  onRefresh?: () => void
  isRefreshing?: boolean
  actions?: React.ReactNode
  showSearch?: boolean
}

export function Header({
  title = 'Executive Operations Dashboard',
  subtitle = 'Real-time satellite detection & maritime attribution monitor',
  onRefresh,
  isRefreshing = false,
  actions,
  showSearch = true,
}: HeaderProps) {
  const router = useRouter()
  const { user, logout, appMode } = useSlickTraceStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [utcTime, setUtcTime] = useState<string>('')

  // Live UTC Clock
  useEffect(() => {
    const update = () => {
      const d = new Date()
      setUtcTime(d.toISOString().replace('T', ' ').substring(11, 19) + ' UTC')
    }
    update()
    const timer = setInterval(update, 1000)
    return () => clearInterval(timer)
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/incidents?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  return (
    <header className="border-b border-slate-800 bg-[#070e1e]/95 backdrop-blur-md sticky top-0 z-20 font-sans select-none">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
        {/* Left: Title & Subtitle */}
        <div className="min-w-0 flex-shrink-0">
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-sm md:text-base text-slate-100 tracking-tight">{title}</h1>
            {appMode === 'demo' ? (
              <span className="badge-demo text-[10px]">DEMO SANDBOX</span>
            ) : (
              <span className="badge-real text-[10px]">REAL MODE</span>
            )}
          </div>
          {subtitle && <p className="text-[11px] text-slate-400 hidden sm:block truncate">{subtitle}</p>}
        </div>

        {/* Center: Investigation Search */}
        {showSearch && (
          <form onSubmit={handleSearch} className="flex-1 max-w-md hidden md:block">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search incidents by case ID, vessel name, MMSI, or region..."
                className="w-full bg-[#040814] border border-slate-800 focus:border-ocean-500 rounded-xl py-1.5 pl-9 pr-8 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-ocean-500 font-mono transition-all"
              />
              <span className="absolute right-2.5 top-2 text-[10px] font-mono text-slate-400 border border-slate-800 rounded px-1">
                /
              </span>
            </div>
          </form>
        )}

        {/* Right: Actions, Live UTC & User Profile */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {actions}

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3 disabled:opacity-50"
              title="Refresh Pipeline Telemetry"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isRefreshing && 'animate-spin text-ocean-400')} />
              <span className="hidden sm:inline">{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
            </button>
          )}

          {/* UTC Clock */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
            <Clock className="w-3 h-3 text-sky-400" />
            <span>{utcTime || 'UTC Live'}</span>
          </div>

          {/* User Profile Badge */}
          <div className="flex items-center gap-2 pl-1 border-l border-slate-800">
            <div className="hidden sm:flex flex-col items-end text-right">
              <span className="text-xs font-semibold text-slate-200 leading-tight">
                {user?.role || 'Lead Investigator'}
              </span>
              <span className="text-[10px] font-mono text-slate-400 truncate max-w-[120px]">
                {user?.email || 'investigator@agency.gov'}
              </span>
            </div>

            <Link
              href="/login"
              onClick={() => logout()}
              className="p-2 rounded-xl bg-slate-900 hover:bg-rose-950/60 hover:text-rose-300 text-slate-400 border border-slate-800 transition-colors"
              title="Sign Out / Switch Identity"
            >
              <LogOut className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  )
}
