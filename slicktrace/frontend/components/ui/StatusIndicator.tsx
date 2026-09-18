import * as React from 'react'

export interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'standby' | 'warning' | 'error' | 'loading'
  label?: string
  pulse?: boolean
  className?: string
}

export function StatusIndicator({
  status,
  label,
  pulse = true,
  className = '',
}: StatusIndicatorProps) {
  const colorMap = {
    online: 'bg-emerald-400',
    offline: 'bg-slate-500',
    standby: 'bg-sky-400',
    warning: 'bg-amber-400',
    error: 'bg-rose-500',
    loading: 'bg-cyan-400',
  }

  const glowMap = {
    online: 'bg-emerald-400/30',
    offline: 'bg-slate-500/20',
    standby: 'bg-sky-400/30',
    warning: 'bg-amber-400/30',
    error: 'bg-rose-500/30',
    loading: 'bg-cyan-400/30',
  }

  return (
    <div className={`inline-flex items-center space-x-2 ${className}`}>
      <span className="relative flex h-2 w-2">
        {pulse && status !== 'offline' && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${glowMap[status]}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${colorMap[status]}`} />
      </span>
      {label && <span className="text-xs font-mono text-slate-300">{label}</span>}
    </div>
  )
}
