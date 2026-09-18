import * as React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean
  variant?: 'default' | 'raised' | 'glow' | 'accent'
}

export function Card({
  className = '',
  hoverEffect = false,
  variant = 'default',
  children,
  ...props
}: CardProps) {
  const variantStyles = {
    default: 'bg-slate-900/80 border-slate-800/80 shadow-md',
    raised: 'bg-slate-900/95 border-slate-700/80 shadow-xl shadow-black/40',
    glow: 'bg-slate-900/90 border-sky-500/30 shadow-lg shadow-sky-950/20',
    accent: 'bg-slate-950 border-cyan-500/40 shadow-xl shadow-cyan-950/20',
  }

  const hoverClass = hoverEffect
    ? 'hover:border-slate-600 hover:shadow-lg transition-all duration-200'
    : ''

  return (
    <div
      className={`rounded-xl border backdrop-blur-md ${variantStyles[variant]} ${hoverClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-4 pb-2 border-b border-slate-800/60 ${className}`} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={`text-sm font-semibold text-slate-100 tracking-tight ${className}`} {...props}>
      {children}
    </h3>
  )
}

export function CardDescription({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={`text-xs text-slate-400 mt-0.5 ${className}`} {...props}>
      {children}
    </p>
  )
}

export function CardContent({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-4 ${className}`} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({
  className = '',
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`p-4 pt-2 border-t border-slate-800/60 flex items-center justify-between ${className}`} {...props}>
      {children}
    </div>
  )
}
