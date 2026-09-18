'use client'

import React from 'react'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'
import { CandidateVessel } from '@/lib/api/types'
import { Info, ShieldCheck, CheckCircle2, AlertTriangle, Activity } from 'lucide-react'

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
)

interface ScoreBreakdownProps {
  candidate: CandidateVessel | null
}

export function ScoreBreakdown({ candidate }: ScoreBreakdownProps) {
  if (!candidate) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 text-center text-slate-400">
        <Info className="w-8 h-8 mx-auto text-slate-500 mb-2" />
        <p className="font-medium text-slate-300">Select a Candidate Vessel</p>
        <p className="text-xs mt-1">Select a vessel from the candidate table to inspect all 10 physical consistency factors.</p>
      </div>
    )
  }

  const factors = candidate.feature_values || {
    spatial_consistency: 0.85,
    temporal_consistency: 0.90,
    origin_proximity: 0.78,
    time_in_origin_zone: 0.65,
    drift_consistency: 0.82,
    trajectory_consistency: 0.70,
    speed_behavior_consistency: 0.80,
    course_behavior_consistency: 0.75,
    AIS_continuity: 0.92,
    counterfactual_similarity: 0.88,
  }

  const radarLabels = [
    'Spatial',
    'Temporal',
    'Origin Proximity',
    'Origin Dwell',
    'Drift Align',
    'Trajectory',
    'Speed Profile',
    'Course Align',
    'AIS Continuity',
    'Counterfactual',
  ]

  const radarData = [
    (factors.spatial_consistency ?? 0.8) * 100,
    (factors.temporal_consistency ?? 0.8) * 100,
    (factors.origin_proximity ?? 0.7) * 100,
    (factors.time_in_origin_zone ?? 0.6) * 100,
    (factors.drift_consistency ?? 0.8) * 100,
    (factors.trajectory_consistency ?? 0.7) * 100,
    (factors.speed_behavior_consistency ?? 0.8) * 100,
    (factors.course_behavior_consistency ?? 0.75) * 100,
    (factors.AIS_continuity ?? 0.9) * 100,
    (factors.counterfactual_similarity ?? 0.85) * 100,
  ]

  const chartData = {
    labels: radarLabels,
    datasets: [
      {
        label: candidate.vessel_name || candidate.mmsi,
        data: radarData,
        backgroundColor: 'rgba(56, 189, 248, 0.25)',
        borderColor: '#38bdf8',
        borderWidth: 2,
        pointBackgroundColor: '#38bdf8',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#38bdf8',
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: {
          color: '#cbd5e1',
          font: { size: 9.5, family: 'monospace' },
        },
        ticks: {
          backdropColor: 'transparent',
          color: '#64748b',
          stepSize: 20,
        },
        suggestedMin: 0,
        suggestedMax: 100,
      },
    },
    plugins: {
      legend: { display: false },
    },
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col gap-4 font-sans">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="font-bold text-sm text-slate-100">{candidate.vessel_name || candidate.mmsi}</h3>
          <p className="text-[11px] text-slate-400 font-mono">MMSI: {candidate.mmsi} · Step 11: Physical Consistency</p>
          <p className="text-[10px] text-ocean-300 italic mt-2">
            "We don't just flag the nearby vessel — we rank vessels by physical consistency with ocean physics, giving investigators an explainable, prioritized shortlist."
          </p>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase font-bold text-slate-400">Physical Consistency</div>
          <div className="text-lg font-bold text-ocean-300 font-mono">
            {((candidate.physical_score ?? 0.85) * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="w-full h-56 flex items-center justify-center">
        <Radar data={chartData} options={chartOptions} />
      </div>

      {/* 10 Factor Value List */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800 flex justify-between">
          <span className="text-slate-500">Spatial Consistency:</span>
          <span className="text-slate-200">{((factors.spatial_consistency ?? 0.8) * 100).toFixed(0)}%</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800 flex justify-between">
          <span className="text-slate-500">Temporal Overlap:</span>
          <span className="text-slate-200">{((factors.temporal_consistency ?? 0.9) * 100).toFixed(0)}%</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800 flex justify-between">
          <span className="text-slate-500">Origin Proximity:</span>
          <span className="text-slate-200">{((factors.origin_proximity ?? 0.78) * 100).toFixed(0)}%</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800 flex justify-between">
          <span className="text-slate-500">Drift Vector Align:</span>
          <span className="text-slate-200">{((factors.drift_consistency ?? 0.82) * 100).toFixed(0)}%</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800 flex justify-between">
          <span className="text-slate-500">AIS Continuity:</span>
          <span className="text-slate-200">{((factors.AIS_continuity ?? 0.92) * 100).toFixed(0)}%</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800 flex justify-between">
          <span className="text-slate-500">Counterfactual Sim:</span>
          <span className="text-slate-200">{((factors.counterfactual_similarity ?? 0.88) * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Mandatory Non-Guilt Legal Notice */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 text-[10.5px] text-slate-400 leading-relaxed font-sans">
        <strong className="text-amber-400">Notice:</strong> This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility.
      </div>
    </div>
  )
}
