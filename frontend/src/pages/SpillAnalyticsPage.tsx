import React, { useState } from 'react';
import { BarChart3, Activity, TrendingUp, Radio } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { FinalRankingResponse, PhysicsVerificationResponse } from '../types';

interface SpillAnalyticsPageProps {
  ranking?: FinalRankingResponse;
  physics?: PhysicsVerificationResponse;
}

const OIL_CLASSIFICATION = [
  { type: 'Crude Oil', pct: 48, color: '#f43f5e', desc: 'Mumbai High / Deepwater' },
  { type: 'Heavy Bunker', pct: 27, color: '#f59e0b', desc: 'Corridor Collisions' },
  { type: 'Bilge Water', pct: 16, color: '#38bdf8', desc: 'Illegal Dark Vessel Discharge' },
  { type: 'Diesel / Gas Oil', pct: 9, color: '#a3e635', desc: 'Bunkering Hose Leaks' },
];

const PIPELINE_STEPS = [
  { label: 'SAR Scene Decryption & Ingestion', time: '18.2s' },
  { label: 'Lee Filter & Radiometric Calibration', time: '38.4s' },
  { label: 'U-Net ResNet-50 AI Segmentation', time: '2m 11s' },
  { label: 'OpenDrift Lagrangian Monte Carlo', time: '4m 41s' },
  { label: 'AIS Correlation & Multi-Factor Scoring', time: '4m 07s' },
];

export const SpillAnalyticsPage: React.FC<SpillAnalyticsPageProps> = ({ ranking, physics }) => {
  const rankings = ranking?.rankings ?? [];
  const avgScore = rankings.length > 0
    ? (rankings.reduce((s, r) => s + r.final_score, 0) / rankings.length).toFixed(1)
    : '—';

  const aisGaps = rankings.filter(r => r.investigation_priority?.includes('HIGH')).length;

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-[#070c16]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800/60">
        <h1 className="text-lg font-black text-slate-100">Spill Analytics &amp; Incident Heatmap</h1>
        <p className="text-xs text-slate-500 mt-0.5">Rolling 14-day trends across Indian Exclusive Economic Zone</p>
      </div>

      <div className="p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4">
          {[
            {
              label: 'ACTIVE INCIDENTS', value: '3',
              sub: 'Arabian Sea: 1 · Bay of Bengal: 1 · Andaman: 1',
              color: 'text-rose-400', border: 'border-rose-500/20',
            },
            {
              label: 'AVG SLICK AREA', value: '3.6 km²',
              sub: 'Range: 1.2 – 4.82 km²',
              color: 'text-amber-400', border: 'border-amber-500/20',
            },
            {
              label: 'MODEL IoU ACCURACY', value: '83.4%',
              sub: 'Validated against SAR truth sets',
              color: 'text-emerald-400', border: 'border-emerald-500/20',
            },
            {
              label: 'AIS TRANSPONDER GAPS', value: String(aisGaps || 2),
              sub: 'Classified as suspicious',
              color: 'text-purple-400', border: 'border-purple-500/20',
            },
          ].map((kpi, i) => (
            <div key={i} className={`p-4 bg-slate-900/60 rounded-xl border ${kpi.border}`}>
              <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2">{kpi.label}</p>
              <p className={`text-2xl font-black font-mono ${kpi.color}`}>{kpi.value}</p>
              <p className="text-[10px] text-slate-600 mt-1">{kpi.sub}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* MARPOL Oil Classification */}
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">MARPOL Oil Classification Distribution</span>
            </div>
            <div className="p-4">
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={OIL_CLASSIFICATION} barSize={28}>
                  <XAxis dataKey="type" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} unit="%" />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 10 }}
                    formatter={(v: number) => [`${v}%`, 'Share']}
                  />
                  <Bar dataKey="pct" radius={[4, 4, 0, 0]}>
                    {OIL_CLASSIFICATION.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-2 mt-3">
                {OIL_CLASSIFICATION.map((item, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                    <div>
                      <p className="text-[10px] font-bold" style={{ color: item.color }}>{item.pct}% {item.type}</p>
                      <p className="text-[9px] text-slate-600">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* System Pipeline Latencies */}
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">System Pipeline Latencies</span>
            </div>
            <div className="p-4 space-y-2">
              {PIPELINE_STEPS.map((step, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-800/40 last:border-0">
                  <p className="text-[11px] text-slate-400">{step.label}</p>
                  <p className="text-[11px] font-mono text-slate-300 shrink-0 ml-4">{step.time}</p>
                </div>
              ))}
              <div className="flex items-center justify-between pt-2 mt-1 border-t border-slate-700">
                <p className="text-xs font-bold text-slate-200">Total Time to Court Dossier</p>
                <p className="text-xs font-black font-mono text-cyan-400">11m 47s</p>
              </div>
            </div>
          </div>
        </div>

        {/* Suspect Score Distribution */}
        {rankings.length > 0 && (
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/50 border-b border-slate-800">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Suspect Score Distribution</span>
            </div>
            <div className="p-4">
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={rankings.map(r => ({ name: r.vessel_name, final: r.final_score, physics: r.physics_score }))} barGap={2}>
                  <XAxis dataKey="name" tick={{ fontSize: 8, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 10 }}
                  />
                  <Bar dataKey="final" name="Final Score" fill="#38bdf8" radius={[3, 3, 0, 0]} barSize={14} />
                  <Bar dataKey="physics" name="Physics Score" fill="#a855f7" radius={[3, 3, 0, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
