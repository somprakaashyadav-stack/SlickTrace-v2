import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { ModeGuard } from '@/components/core/ModeGuard'
import { Toaster } from 'sonner'

export const metadata: Metadata = {
  title: 'SlickTrace v2 — Maritime Oil Spill Investigation Platform',
  description: 'Professional satellite-based oil-spill investigation and vessel attribution decision-support platform.',
  icons: { icon: '/favicon.ico' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased bg-slate-950 text-slate-100">
        <Providers>
          <ModeGuard />
          {children}
          <Toaster position="top-right" theme="dark" richColors />
        </Providers>
      </body>
    </html>
  )
}
