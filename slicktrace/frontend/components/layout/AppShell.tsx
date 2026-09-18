'use client'

import React from 'react'
import { Topbar } from './Topbar'
import { Sidebar } from './Sidebar'

export interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-[#040814] text-slate-100 font-sans selection:bg-sky-500/30 selection:text-sky-200">
      <Topbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 relative bg-radial-gradient">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
