import * as React from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'
import { Button } from './Button'

export interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'System Anomaly Detected',
  message,
  onRetry,
  className = '',
}: ErrorStateProps) {
  return (
    <div
      className={`p-5 rounded-xl border border-rose-500/30 bg-rose-950/20 backdrop-blur-sm ${className}`}
    >
      <div className="flex items-start space-x-3">
        <div className="p-2 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-400 shrink-0">
          <AlertTriangle className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-rose-300 uppercase tracking-wider">{title}</h4>
          <p className="text-xs text-slate-300 mt-1 font-mono break-words leading-relaxed">{message}</p>
          {onRetry && (
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                leftIcon={RotateCcw}
                className="border-rose-500/40 text-rose-300 hover:bg-rose-500/10"
              >
                Retry Diagnostics
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
