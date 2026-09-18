import * as React from 'react'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'real' | 'demo' | 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'outline'
  size?: 'sm' | 'md'
  dot?: boolean
}

export function Badge({
  className = '',
  variant = 'neutral',
  size = 'md',
  dot = false,
  children,
  ...props
}: BadgeProps) {
  const sizeStyles = {
    sm: 'text-[10px] px-2 py-0.5 font-mono gap-1',
    md: 'text-xs px-2.5 py-0.5 font-mono gap-1.5',
  }

  const variantStyles = {
    real: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40 shadow-sm shadow-emerald-950/40',
    demo: 'bg-amber-950/80 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-950/40',
    success: 'bg-emerald-950/70 text-emerald-300 border-emerald-600/30',
    warning: 'bg-amber-950/70 text-amber-300 border-amber-600/30',
    danger: 'bg-rose-950/70 text-rose-300 border-rose-600/30',
    info: 'bg-sky-950/70 text-sky-300 border-sky-600/30',
    neutral: 'bg-slate-800/80 text-slate-300 border-slate-700/60',
    outline: 'bg-transparent text-slate-300 border-slate-700',
  }

  const dotColors = {
    real: 'bg-emerald-400',
    demo: 'bg-amber-400',
    success: 'bg-emerald-400',
    warning: 'bg-amber-400',
    danger: 'bg-rose-400',
    info: 'bg-sky-400',
    neutral: 'bg-slate-400',
    outline: 'bg-slate-400',
  }

  return (
    <span
      className={`inline-flex items-center font-medium rounded-md border tracking-wider uppercase select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColors[variant]}`} />
      )}
      {children}
    </span>
  )
}
