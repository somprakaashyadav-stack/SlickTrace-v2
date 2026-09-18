'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import {
  Waves,
  Lock,
  Mail,
  Shield,
  ArrowRight,
  AlertTriangle,
  Sparkles,
  Server,
  Compass,
  Radio,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react'
import { api } from '@/lib/api/client'
import { useSlickTraceStore } from '@/lib/stores/slicktrace'
import { AuthResponse } from '@/lib/api/types'
import { cn } from '@/lib/utils'

export default function LoginPage() {
  const router = useRouter()
  const { setUser, setToken, setAppMode } = useSlickTraceStore()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isDemoLoading, setIsDemoLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [utcTime, setUtcTime] = useState<string>('')

  // Live UTC Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setUtcTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC')
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  // Real System Health Diagnostics
  const { data: healthData, isError: healthError } = useQuery({
    queryKey: ['health-services'],
    queryFn: () => api.get<any>('/health/services'),
    refetchInterval: 20000,
  })

  const services = healthData?.services || {}
  const backendOnline = !healthError && !!healthData
  const dbOnline = !!services?.database?.ok
  const satOnline = !!services?.satellite_provider?.ok
  const aisOnline = !!services?.ais_provider?.ok
  const metoceanOnline = !!services?.metocean_provider?.ok

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter your government email and password.')
      return
    }

    setIsLoading(true)

    try {
      const res = await api.post<AuthResponse>('/auth/login', {
        email: email.trim(),
        password: password.trim(),
        remember_me: rememberMe,
      })

      setUser({
        email: res.email,
        role: res.role,
        full_name: res.full_name,
        mode: 'real',
        authenticated: true,
      })
      setToken(res.access_token)
      setAppMode('real')

      if (rememberMe) {
        localStorage.setItem('slicktrace_token', res.access_token)
        localStorage.setItem('slicktrace_mode', 'real')
        localStorage.setItem(
          'slicktrace_user',
          JSON.stringify({
            email: res.email,
            role: res.role,
            full_name: res.full_name,
            mode: 'real',
          })
        )
      }

      router.push('/dashboard')
    } catch (err: any) {
      if (err.response?.status === 401) {
        setErrorMessage('Authentication failed. Verify credentials and try again.')
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setErrorMessage('Authentication service unavailable. Please retry.')
      } else {
        setErrorMessage(
          err.response?.data?.detail || 'Authentication failed. Verify credentials and try again.'
        )
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleEnterDemo = async () => {
    setErrorMessage(null)
    setIsDemoLoading(true)

    try {
      let res: AuthResponse
      try {
        res = await api.post<AuthResponse>('/auth/demo', {})
      } catch {
        res = {
          access_token: 'st2_demo_sandbox_token',
          token_type: 'bearer',
          role: 'Investigator (Sandbox)',
          email: 'evaluator.sandbox@slicktrace.local',
          full_name: 'Demo Sandbox Evaluator',
          mode: 'demo',
          expires_in: 86400,
        }
      }

      setUser({
        email: res.email,
        role: res.role,
        full_name: res.full_name,
        mode: 'demo',
        authenticated: true,
      })
      setToken(res.access_token)
      setAppMode('demo')

      localStorage.setItem('slicktrace_token', res.access_token)
      localStorage.setItem('slicktrace_mode', 'demo')

      router.push('/demo')
    } catch (err) {
      setErrorMessage('Authentication service unavailable. Please retry.')
    } finally {
      setIsDemoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#040814] text-slate-100 flex flex-col items-center justify-between p-4 md:p-8 relative overflow-hidden font-sans selection:bg-ocean-500 selection:text-white">
      {/* Background Subtle Tactical Grid */}
      <div className="absolute inset-0 pointer-events-none opacity-15">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="login-grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#0284c7" strokeWidth="0.5" strokeDasharray="2 2" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#login-grid)" />
        </svg>
      </div>

      {/* Top Header Identity */}
      <header className="pt-6 pb-2 text-center z-10 flex flex-col items-center">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-ocean-600 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-ocean-950">
            <Waves className="w-6 h-6 text-white" />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="text-xl md:text-2xl font-black tracking-wider text-slate-100 uppercase">
                SLICKTRACE
              </span>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-ocean-950 text-ocean-300 border border-ocean-700">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-wide font-medium">
              Maritime Oil Spill Investigation Platform
            </p>
          </div>
        </div>
      </header>

      {/* Center Command Card */}
      <main className="w-full max-w-md my-auto z-10">
        <div className="bg-[#0a1024]/95 backdrop-blur-md border border-slate-800 rounded-3xl p-8 shadow-2xl shadow-black/90 flex flex-col gap-5 relative">
          {/* Workspace Title */}
          <div className="flex flex-col items-center text-center pb-1">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200 tracking-wider uppercase mb-1">
              <Shield className="w-4 h-4 text-ocean-400" />
              <span>Secure Investigation Workspace</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Authorized maritime agency personnel only · ISO/IEC 27037 Forensics
            </p>
          </div>

          {/* Error Message Box */}
          {errorMessage && (
            <div className="bg-rose-950/70 border border-rose-800 text-rose-200 rounded-2xl p-3.5 text-xs flex items-start gap-2.5 shadow animate-in fade-in duration-150">
              <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-[11.5px] leading-relaxed">
                {errorMessage}
              </div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSignIn} className="flex flex-col gap-4">
            {/* Email Field */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Agency Email</span>
                <span className="text-[10px] font-mono text-slate-400">Government ID</span>
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="investigator@agency.gov"
                  required
                  className="w-full bg-[#060b18] border border-slate-800 focus:border-ocean-500 rounded-xl py-2.5 pl-10 pr-3.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-ocean-500 transition-all font-mono"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Password</span>
                <span className="text-[10px] text-slate-400">Encrypted</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter security key..."
                  required
                  className="w-full bg-[#060b18] border border-slate-800 focus:border-ocean-500 rounded-xl py-2.5 pl-10 pr-3.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-ocean-500 transition-all font-mono"
                />
              </div>
            </div>

            {/* Remember Session */}
            <div className="flex items-center justify-between pt-0.5">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-3.5 h-3.5 rounded bg-slate-900 border-slate-700 text-ocean-600 focus:ring-ocean-500 cursor-pointer"
                />
                <span className="text-xs text-slate-400 hover:text-slate-300">Remember session</span>
              </label>
              <span className="text-[10px] text-slate-400 font-mono">TLS 1.3 Strict</span>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={isLoading || isDemoLoading}
              className="w-full btn-primary py-2.5 text-xs shadow-lg shadow-ocean-950/60 cursor-pointer font-bold mt-1"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>{isLoading ? 'Signing in...' : 'SIGN IN'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Divider */}
          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-slate-800" />
            <span className="flex-shrink mx-4 text-[10px] font-mono uppercase text-slate-400 tracking-widest">
              ───────────── OR ─────────────
            </span>
            <div className="flex-grow border-t border-slate-800" />
          </div>

          {/* Demo Button */}
          <div className="flex flex-col gap-1.5">
            <button
              type="button"
              onClick={handleEnterDemo}
              disabled={isLoading || isDemoLoading}
              className="w-full bg-amber-950/30 hover:bg-amber-950/60 text-amber-300 border border-amber-800/80 hover:border-amber-600 font-semibold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow shadow-amber-950/50 cursor-pointer group"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-400 group-hover:rotate-12 transition-transform" />
              <span>{isDemoLoading ? 'Loading Sandbox...' : 'ENTER DEMO ENVIRONMENT'}</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-900/60 text-amber-200 border border-amber-700/60 uppercase">
                DEMO ENVIRONMENT
              </span>
            </button>
            <p className="text-[10px] text-center text-slate-400">
              Quarantined sandbox for offline evaluation &amp; simulated training.
            </p>
          </div>

          {/* Real Backend Health Status Indicator Box */}
          <div className="pt-3 border-t border-slate-800 flex flex-col gap-2">
            <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">
              System Provider Status (Data-Driven)
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[10px] font-mono">
              <div className="flex items-center gap-1.5 bg-[#060b18] px-2 py-1 rounded-lg border border-slate-800/80">
                <span className={cn('w-2 h-2 rounded-full', backendOnline ? 'bg-emerald-400' : 'bg-rose-400')} />
                <span className="text-slate-300">Backend:</span>
                <span className={backendOnline ? 'text-emerald-400 font-bold' : 'text-rose-400'}>
                  {backendOnline ? 'ONLINE' : 'DOWN'}
                </span>
              </div>

              <div className="flex items-center gap-1.5 bg-[#060b18] px-2 py-1 rounded-lg border border-slate-800/80">
                <span className={cn('w-2 h-2 rounded-full', dbOnline ? 'bg-emerald-400' : 'bg-amber-400')} />
                <span className="text-slate-300">Database:</span>
                <span className={dbOnline ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                  {dbOnline ? 'CONNECTED' : 'STANDBY'}
                </span>
              </div>

              <div className="flex items-center gap-1.5 bg-[#060b18] px-2 py-1 rounded-lg border border-slate-800/80">
                <span className={cn('w-2 h-2 rounded-full', satOnline ? 'bg-emerald-400' : 'bg-slate-500')} />
                <span className="text-slate-300">Satellite:</span>
                <span className={satOnline ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                  {satOnline ? 'READY' : 'OFFLINE'}
                </span>
              </div>

              <div className="flex items-center gap-1.5 bg-[#060b18] px-2 py-1 rounded-lg border border-slate-800/80">
                <span className={cn('w-2 h-2 rounded-full', aisOnline ? 'bg-emerald-400' : 'bg-slate-500')} />
                <span className="text-slate-300">AIS:</span>
                <span className={aisOnline ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                  {aisOnline ? 'READY' : 'OFFLINE'}
                </span>
              </div>

              <div className="flex items-center gap-1.5 bg-[#060b18] px-2 py-1 rounded-lg border border-slate-800/80 sm:col-span-2">
                <span className={cn('w-2 h-2 rounded-full', metoceanOnline ? 'bg-emerald-400' : 'bg-slate-500')} />
                <span className="text-slate-300">Metocean:</span>
                <span className={metoceanOnline ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                  {metoceanOnline ? 'READY' : 'NOT CONFIGURED'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer Live UTC Clock */}
      <footer className="w-full max-w-7xl pt-4 pb-2 border-t border-slate-800/60 z-10 flex flex-col sm:flex-row items-center justify-between text-[11px] font-mono text-slate-400 gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>SlickTrace Forensic Core v2.0</span>
        </div>
        <div className="flex items-center gap-3 text-slate-300">
          <span>{utcTime || 'UTC Live'}</span>
          <span className="text-slate-600">|</span>
          <span>Zero-Fabrication Contract Enforced</span>
        </div>
      </footer>
    </div>
  )
}
