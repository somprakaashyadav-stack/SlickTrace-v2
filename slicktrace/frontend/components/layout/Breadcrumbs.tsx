import * as React from 'react'
import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[]
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center space-x-1.5 text-xs font-mono text-slate-400">
      <Link
        href="/dashboard"
        className="hover:text-slate-200 transition-colors flex items-center"
      >
        <Home className="w-3.5 h-3.5" />
      </Link>
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        return (
          <React.Fragment key={index}>
            <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
            {item.href && !isLast ? (
              <Link href={item.href} className="hover:text-slate-200 transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? 'text-sky-400 font-semibold' : ''}>
                {item.label}
              </span>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}
