'use client'

import { useEffect, useState } from 'react'
import { Activity, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { useSlickTraceStore } from '@/lib/stores/slicktrace'

interface TaskProgressPanelProps {
  incidentId: string
}

export function TaskProgressPanel({ incidentId }: TaskProgressPanelProps) {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<Array<{ time: string; text: string; type: string }>>([])
  const updateProgress = useSlickTraceStore((s) => s.updateProgress)

  useEffect(() => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws'}/${incidentId}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setConnected(true)
      setMessages((prev) => [
        ...prev,
        { time: new Date().toLocaleTimeString(), text: 'Connected to investigation telemetry', type: 'info' },
      ])
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'progress') {
          updateProgress(data.task, { status: data.status, message: data.message })
          setMessages((prev) => [
            ...prev,
            { time: new Date().toLocaleTimeString(), text: data.message || `${data.task}: ${data.status}`, type: data.status },
          ])
        }
      } catch (err) {
        console.error('WS parse error', err)
      }
    }

    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    return () => {
      ws.close()
    }
  }, [incidentId, updateProgress])

  return (
    <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-4 shadow-lg flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-700 mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-400" />
          <h3 className="font-semibold text-sm text-slate-200">Execution Telemetry</h3>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}
          />
          <span className="text-slate-400 font-mono text-[10pt]">
            {connected ? 'SOCKET LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-xs max-h-48">
        {messages.length === 0 ? (
          <div className="text-slate-500 py-6 text-center italic">
            Awaiting task dispatch...
          </div>
        ) : (
          messages.map((m, idx) => (
            <div key={idx} className="flex items-start gap-2 text-slate-300">
              <span className="text-slate-500 flex-shrink-0">[{m.time}]</span>
              {m.type === 'running' && <Loader2 className="w-3.5 h-3.5 text-brand-400 animate-spin flex-shrink-0 mt-0.5" />}
              {m.type === 'done' && <CheckCircle className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />}
              {m.type === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />}
              <span className="break-all">{m.text}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
