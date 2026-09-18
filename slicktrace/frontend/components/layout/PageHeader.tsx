import * as React from 'react'

export interface PageHeaderProps {
  title: string
  description?: string
  badge?: React.ReactNode
  actions?: React.ReactNode
  breadcrumbs?: React.ReactNode
}

export function PageHeader({
  title,
  description,
  badge,
  actions,
  breadcrumbs,
}: PageHeaderProps) {
  return (
    <div className="space-y-2 mb-6">
      {breadcrumbs && <div className="mb-2">{breadcrumbs}</div>}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="text-lg sm:text-xl font-bold text-slate-100 tracking-tight font-sans">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center space-x-2.5 shrink-0">{actions}</div>}
      </div>
    </div>
  )
}
