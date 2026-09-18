'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Shield, Radio, Clock, User, Compass, ExternalLink, Activity } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { StatusIndicator } from '@/components/ui/StatusIndicator'
import { useSlickTraceStore } from '@/lib/stores/slicktrace'

export function Topbar() {
  const [utcTime, setUtcTime] = useState<string>('')
  const [systemHealth, setSystemHealth] = useState<'online' | 'offline' | 'loading'>('loading')
  const { user, appMode: mode, token, logout, activeIncident: currentIncident } = useSlickTraceStore()

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setUtcTime(now.toUTCString().slice(17, 25) + ' UTC')
    }
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
        const baseUrl = apiUrl.replace('/api/v1', '')
        const res = await fetch(`${baseUrl}/health`, { method: 'GET' })
        if (res.ok) {
          setSystemHealth('online')
        } else {
          setSystemHealth('offline')
        }
      } catch (err) {
        setSystemHealth('offline')
      }
    }
    checkHealth()
    const poll = setInterval(checkHealth, 30000)
    return () => clearInterval(poll)
  }, [])

  return (
    <header className="h-14 bg-slate-950/95 border-b border-slate-800/80 px-4 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md">
      {/* Left: Brand / System Title */}
      <div className="flex items-center space-x-3 shrink-0">
        <Link href="/dashboard" className="flex items-center space-x-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-sky-950/80 border border-sky-500/40 flex items-center justify-center text-sky-400 group-hover:border-sky-400 group-hover:bg-sky-900/60 transition-all shadow-sm shadow-sky-950/50">
            <Compass className="w-4 h-4 text-sky-400 group-hover:rotate-45 transition-transform duration-300" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="text-xs font-bold font-mono tracking-widest text-slate-100 group-hover:text-sky-300 transition-colors">
                SLICKTRACE
              </span>
              <span className="text-[10px] font-mono text-sky-400 bg-sky-950/80 px-1 py-0.2 rounded border border-sky-600/30">
                v2.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium tracking-tight">
              Maritime Oil Spill Platform
            </p>
          </div>
        </Link>
      </div>

      {/* Center: Current Investigation Context */}
      <div className="hidden md:flex items-center space-x-2 px-3 py-1 rounded-lg bg-slate-900/80 border border-slate-800/80 max-w-md">
        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider shrink-0">
          Investigation:
        </span>
        {currentIncident ? (
          <Link
            href={`/incidents/${currentIncident.id}`}
            className="text-xs font-mono font-medium text-sky-300 hover:text-sky-200 truncate flex items-center space-x-1"
          >
            <span>{currentIncident.case_id || currentIncident.title}</span>
            <ExternalLink className="w-3 h-3 text-sky-400 shrink-0 ml-1" />
          </Link>
        ) : (
          <span className="text-xs font-mono text-slate-400 italic">
            No active investigation
          </span>
        )}
      </div>

      {/* Right: Operational Controls & Telemetry */}
      <div className="flex items-center space-x-3">
        {/* Mode Indicator */}
        <Badge variant={mode === 'real' ? 'real' : 'demo'} dot size="sm">
          {mode === 'real' ? 'REAL MODE' : 'DEMO MODE'}
        </Badge>

        {/* Backend System Health */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2 py-1 rounded-md bg-slate-900/60 border border-slate-800">
          <StatusIndicator
            status={systemHealth}
            label={systemHealth === 'online' ? 'SYS OPERATIONAL' : 'SYS OFFLINE'}
            pulse={systemHealth === 'online'}
          />
        </div>

        {/* Live UTC Clock */}
        <div className="hidden lg:flex items-center space-x-1.5 text-slate-300 text-xs font-mono px-2 py-1 rounded-md bg-slate-900/60 border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>{utcTime || '--:--:-- UTC'}</span>
        </div>

        {/* User Badge / Logout */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
          <div className="flex items-center space-x-1.5 text-xs text-slate-300 font-mono">
            <div className="w-6 h-6 rounded-md bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <User className="w-3.5 h-3.5" />
            </div>
            <span className="hidden sm:inline-block max-w-[100px] truncate">
              {user?.full_name || user?.role || 'Investigator'}
            </span>
          </div>
          {token && (
            <button
              onClick={logout}
              title="Sign Out"
              className="text-[10px] font-mono text-slate-400 hover:text-rose-400 px-1.5 py-0.5 rounded hover:bg-slate-800/80 transition-colors"
            >
              Exit
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
