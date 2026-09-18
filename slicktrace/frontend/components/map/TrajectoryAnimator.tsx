'use client'

import React, { useState, useEffect } from 'react'
import { Play, Pause, RotateCcw, Clock, FastForward } from 'lucide-react'

interface TrajectoryAnimatorProps {
  totalHours?: number
  durations?: number[]
  onHourChange?: (hour: number) => void
  onDurationSelect?: (duration: number) => void
}

export function TrajectoryAnimator({
  totalHours = 24,
  durations = [4, 8, 12, 24],
  onHourChange,
  onDurationSelect,
}: TrajectoryAnimatorProps) {
  const [currentHour, setCurrentHour] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState<number>(1) // 1x, 2x, 4x

  useEffect(() => {
    let interval: any = null
    if (isPlaying) {
      const delay = Math.max(150, Math.round(600 / speed))
      interval = setInterval(() => {
        setCurrentHour((prev) => {
          const next = prev + 1
          if (next > totalHours) {
            setIsPlaying(false)
            return totalHours
          }
          if (onHourChange) onHourChange(next)
          return next
        })
      }, delay)
    }
    return () => clearInterval(interval)
  }, [isPlaying, totalHours, speed, onHourChange])

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10)
    setCurrentHour(val)
    if (onHourChange) onHourChange(val)
  }

  const handleSelectHorizon = (h: number) => {
    setCurrentHour(h)
    if (onHourChange) onHourChange(h)
    if (onDurationSelect) onDurationSelect(h)
  }

  return (
    <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-3 shadow flex flex-col gap-2.5">
      {/* Header telemetry and quick horizon presets */}
      <div className="flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center gap-1.5 font-medium">
          <Clock className="w-3.5 h-3.5 text-ocean-400" />
          <span>Lagrangian Reverse Drift Playback</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-ocean-300 bg-ocean-950/60 px-2 py-0.5 rounded border border-ocean-800 text-[11px]">
            T - {currentHour}h (Backward in Time)
          </span>

          <div className="flex items-center bg-slate-900/80 rounded-lg p-0.5 border border-slate-700">
            {durations.map((d) => (
              <button
                key={d}
                onClick={() => handleSelectHorizon(d)}
                className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors ${
                  currentHour === d
                    ? 'bg-ocean-600 text-white font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                -{d}h
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Playback Controls & Slider */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>

        <button
          onClick={() => {
            setIsPlaying(false)
            setCurrentHour(0)
            if (onHourChange) onHourChange(0)
          }}
          className="p-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
          title="Reset to T0 (Detection Time)"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <input
          type="range"
          min="0"
          max={totalHours}
          value={currentHour}
          onChange={handleSliderChange}
          className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-ocean-400"
        />

        <button
          onClick={() => setSpeed(speed === 1 ? 2 : speed === 2 ? 4 : 1)}
          className="px-1.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 text-[10px] font-mono flex items-center gap-1"
          title="Playback Speed"
        >
          <FastForward className="w-3 h-3 text-ocean-400" />
          <span>{speed}x</span>
        </button>

        <span className="text-xs text-slate-400 font-mono flex-shrink-0">
          -{totalHours}h
        </span>
      </div>
    </div>
  )
}
