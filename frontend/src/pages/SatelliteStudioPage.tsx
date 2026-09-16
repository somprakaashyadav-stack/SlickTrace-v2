import React, { useState } from 'react';
import { Satellite, ChevronLeft, ChevronRight, ExternalLink, Info } from 'lucide-react';

const SATELLITES = [
  { name: 'Sentinel-1A', type: 'RADAR', active: false },
  { name: 'Sentinel-1C', type: 'RADAR', active: false },
  { name: 'Sentinel-2A', type: 'OPTICAL', active: true, badge: 'ON MAP' },
  { name: 'Sentinel-2B', type: 'OPTICAL', active: false },
  { name: 'ISRO NISAR', type: 'RADAR', active: false },
  { name: 'EOS-04 (RISAT-1A)', type: 'RADAR', active: false },
];

const SPECTRAL_LAYERS = [
  { label: 'SAR Backscatter (VV dB)', color: 'cyan', active: true },
  { label: 'Capillary Damping', color: 'blue', active: true },
  { label: 'SAR Cross-Pol (VH dB)', color: 'slate', active: false },
  { label: 'Vessel Scattering', color: 'slate', active: false },
  { label: 'Sentinel-1 OCN (In-Situ Wind)', color: 'slate', active: false },
  { label: 'In Situ 4.2 m/s', color: 'slate', active: false },
  { label: 'SWIR Hydrocarbon Index', color: 'slate', active: false },
  { label: 'Emulsified Oil', color: 'slate', active: false },
  { label: 'Floating Algae Index (FAI)', color: 'slate', active: false },
  { label: 'Look-Alike Filter', color: 'slate', active: false },
];

const CONFIDENCE_SCORES = [
  { label: 'U-Net ResNet-50 AI Segment', score: 0.87, desc: 'Val IoU 0.83 on Sentinel-1 SAR benchmarks' },
  { label: 'ERA5 Wind Speed Window', score: 0.91, desc: '4.2 m/s: strictly inside [3.0, 12.0] m/s validity window' },
  { label: 'Biogenic Algal Exclusion', score: 0.78, desc: 'Chlorophyll-a below bloom threshold (MODIS check)' },
];

export const SatelliteStudioPage: React.FC = () => {
  const [selectedSat, setSelectedSat] = useState(2); // Sentinel-2A
  const [date, setDate] = useState('2024-11-14');
  const [cloudFilter, setCloudFilter] = useState(30);
  const [opacity, setOpacity] = useState(92);
  const [activeSpectral, setActiveSpectral] = useState<Set<number>>(new Set([0, 1]));
  const [splitPos, setSplitPos] = useState(50);

  const toggleSpectral = (i: number) => {
    setActiveSpectral(prev => {
      const n = new Set(prev);
      n.has(i) ? n.delete(i) : n.add(i);
      return n;
    });
  };

  const compositeScore = (
    (CONFIDENCE_SCORES.reduce((sum, s) => sum + s.score, 0) / CONFIDENCE_SCORES.length)
  ).toFixed(2);

  return (
    <div className="flex h-full overflow-hidden bg-[#070c16]">
      {/* Left Panel */}
      <div className="w-80 border-r border-slate-800/60 flex flex-col overflow-y-auto shrink-0">
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-800/60 bg-slate-900/50">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <Satellite className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-slate-200">ISRO Bhoonidhi &amp; Copernicus</span>
            </div>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">ONLINE</span>
          </div>
          <p className="text-[9px] text-slate-500">User: KRISHNA KANT · NRSC Oper.Data Node</p>
        </div>

        {/* Date + Cloud */}
        <div className="px-4 py-3 border-b border-slate-800/60">
          <div className="flex items-center gap-2">
            <button className="p-1 hover:bg-slate-800 rounded"><ChevronLeft className="w-3 h-3 text-slate-400" /></button>
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              className="flex-1 bg-slate-800 text-[10px] text-slate-300 rounded px-2 py-1 border border-slate-700 outline-none"
            />
            <button className="p-1 hover:bg-slate-800 rounded"><ChevronRight className="w-3 h-3 text-slate-400" /></button>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-[10px] text-slate-500">Max Cloud Cover</span>
            <span className="text-[10px] font-bold text-amber-400">{cloudFilter}%</span>
          </div>
          <input
            type="range" min={0} max={100} value={cloudFilter}
            onChange={e => setCloudFilter(+e.target.value)}
            className="w-full h-1 mt-1 accent-amber-500"
          />
        </div>

        {/* Satellite Missions */}
        <div className="px-4 py-3 border-b border-slate-800/60 flex-1">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Satellite Missions ({SATELLITES.length})</p>
            <span className="text-[9px] text-slate-600">Bhoonidhi/CISE</span>
          </div>
          <div className="space-y-1">
            {SATELLITES.map((sat, i) => (
              <button
                key={i}
                onClick={() => setSelectedSat(i)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors ${
                  selectedSat === i ? 'bg-cyan-500/10 border border-cyan-500/30' : 'hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${selectedSat === i ? 'bg-cyan-400' : 'bg-slate-600'}`} />
                  <span className={`text-[11px] font-medium ${selectedSat === i ? 'text-slate-200' : 'text-slate-400'}`}>{sat.name}</span>
                  {sat.badge && <span className="text-[8px] px-1 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-bold">{sat.badge}</span>}
                </div>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                  sat.type === 'RADAR' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
                }`}>{sat.type}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Sensor Mode & Opacity */}
        <div className="px-4 py-3 border-t border-slate-800/60">
          <div className="flex items-center justify-between mb-1">
            <p className="text-[10px] text-slate-500">Sensor Modes (3)</p>
            <span className="text-[9px] text-slate-600">Physical Channel</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-800/60 rounded mb-3">
            <span className="text-[10px] text-slate-300 font-medium">C-SAR</span>
            <span className="text-[9px] text-slate-500">S-/Ku C-band</span>
          </div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-slate-500">Layer Opacity</span>
            <span className="text-[10px] font-mono text-cyan-400">{opacity}%</span>
          </div>
          <input
            type="range" min={0} max={100} value={opacity}
            onChange={e => setOpacity(+e.target.value)}
            className="w-full h-1 accent-cyan-500"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Page Header */}
        <div className="px-6 py-3 border-b border-slate-800/60 flex items-center justify-between">
          <div>
            <h1 className="text-sm font-black text-slate-100">Varuna-Drishti Satellite Studio &amp; SAR Look-Alike Validation</h1>
            <p className="text-[10px] text-slate-500">Vedic maritime surveillance · Mumbai High Offshore Basin (18.743°N, 71.218°E) · Calibrated SAR backscatter cross-sections &amp; look-alike suppression</p>
          </div>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700/60 border border-slate-600/40 text-slate-300 text-[10px] font-bold hover:border-cyan-500/30 transition-colors">
              <ExternalLink className="w-3 h-3" /> Copernicus Browser
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 text-white text-[10px] font-bold hover:bg-cyan-500 transition-colors">
              Drift Analysis →
            </button>
          </div>
        </div>

        {/* Mission tabs */}
        <div className="px-6 py-2 border-b border-slate-800/60 flex gap-2">
          {['Sentinel-1 (SAR)', 'Sentinel-2 (Optical)', 'Sentinel-3 / EOS-04', 'Sentinel-6 / NISAR'].map((tab, i) => (
            <button key={i} className={`px-3 py-1 rounded text-[10px] font-bold transition-colors ${i === 0 ? 'bg-cyan-600 text-white' : 'text-slate-500 hover:text-slate-300'}`}>
              {tab}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2 text-[9px] font-mono text-slate-600">
            <span>Sentinel-1A IW GRD</span>·<span>C-SAR 5.4 GHz</span>·<span>Descending Orbit</span>·<span>10m Res</span>
          </div>
        </div>

        {/* Spectral Layer Pills */}
        <div className="px-4 py-2 border-b border-slate-800/60 flex flex-wrap gap-1.5">
          {SPECTRAL_LAYERS.map((layer, i) => (
            <button
              key={i}
              onClick={() => toggleSpectral(i)}
              className={`flex items-center gap-1 px-2 py-1 rounded-full text-[9px] font-bold transition-colors ${
                activeSpectral.has(i)
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  : 'bg-slate-800/60 text-slate-500 border border-slate-700/40 hover:text-slate-300'
              }`}
            >
              {activeSpectral.has(i) && <span className="w-1 h-1 rounded-full bg-cyan-400" />}
              {layer.label}
            </button>
          ))}
        </div>

        {/* Main View Split */}
        <div className="flex flex-1 overflow-hidden">
          {/* Dual Pane SAR Viewer */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 flex items-center gap-3 border-b border-slate-800/60">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Dual-Pane Split: Raw Real Satellite Photo (Left) vs AI U-Net Detection (Right)</span>
              <div className="ml-auto flex items-center gap-2 text-[9px] text-slate-500">
                <span>Incident SAR Scene (Mumbai High)</span>
                <span>Drag handle to inspect</span>
              </div>
            </div>
            {/* Dual pane with slider */}
            <div className="flex-1 relative bg-slate-950 overflow-hidden select-none">
              {/* Raw SAR - Left */}
              <div className="absolute inset-0 flex items-center justify-center" style={{ clipPath: `inset(0 ${100 - splitPos}% 0 0)` }}>
                <div className="w-full h-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center relative">
                  {/* Simulated SAR texture */}
                  <div className="absolute inset-0 opacity-40"
                    style={{ backgroundImage: 'radial-gradient(ellipse 60% 40% at 40% 55%, #111 0%, transparent 70%), radial-gradient(ellipse 30% 20% at 55% 50%, #0a0a0a 0%, transparent 60%)' }}
                  />
                  <div className="absolute bottom-8 left-8 px-2 py-1 rounded bg-slate-900/80 border border-slate-700">
                    <span className="text-[9px] font-mono text-slate-400 uppercase tracking-wider">Raw Real SAR Photo (IB Backscatter)</span>
                  </div>
                  {/* dB annotation */}
                  <div className="absolute top-1/2 left-1/3 px-2 py-1 rounded bg-amber-500/90 text-[9px] font-mono text-black font-bold">
                    σ0 Damping: −8.4 dB
                  </div>
                </div>
              </div>

              {/* U-Net Detection - Right */}
              <div className="absolute inset-0 flex items-center justify-center" style={{ clipPath: `inset(0 0 0 ${splitPos}%)` }}>
                <div className="w-full h-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center relative">
                  <div className="absolute inset-0 opacity-40"
                    style={{ backgroundImage: 'radial-gradient(ellipse 60% 40% at 40% 55%, #111 0%, transparent 70%)' }}
                  />
                  {/* Detection overlay */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <div className="relative">
                      <div className="w-48 h-20 rounded-full border-2 border-cyan-400 bg-cyan-400/15 blur-sm" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="px-3 py-1 rounded bg-cyan-900/90 border border-cyan-400/60 text-[9px] font-mono font-bold text-cyan-300">
                          U-NET DETECTED SLICK: 4.82 km²
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="absolute bottom-8 left-8 px-2 py-1 rounded bg-slate-900/80 border border-slate-700">
                    <span className="text-[9px] font-mono text-cyan-400 uppercase tracking-wider">Real Photo + AI U-Net Detection Mask</span>
                  </div>
                </div>
              </div>

              {/* Drag Handle */}
              <div
                className="absolute top-0 bottom-0 w-1 bg-white/20 cursor-col-resize z-10 flex items-center"
                style={{ left: `${splitPos}%` }}
                onMouseDown={(e) => {
                  const rect = e.currentTarget.parentElement!.getBoundingClientRect();
                  const onMove = (ev: MouseEvent) => setSplitPos(Math.min(90, Math.max(10, ((ev.clientX - rect.left) / rect.width) * 100)));
                  const onUp = () => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
                  document.addEventListener('mousemove', onMove);
                  document.addEventListener('mouseup', onUp);
                }}
              >
                <div className="w-5 h-8 bg-white/30 rounded-full -ml-2 border border-white/20 flex items-center justify-center">
                  <div className="flex gap-0.5">
                    <div className="w-0.5 h-3 bg-white/60 rounded-full" />
                    <div className="w-0.5 h-3 bg-white/60 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel — Confidence */}
          <div className="w-64 border-l border-slate-800/60 flex flex-col overflow-y-auto shrink-0">
            <div className="px-4 py-3 border-b border-slate-800/60">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">☑ Multi-Factor Confidence Assessment</p>
            </div>
            <div className="p-4 space-y-4">
              {CONFIDENCE_SCORES.map((cs, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-[10px] font-bold text-slate-300">{cs.label}</p>
                    <p className="text-sm font-black font-mono text-emerald-400">{cs.score.toFixed(2)}</p>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden mb-1">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${cs.score * 100}%` }} />
                  </div>
                  <p className="text-[9px] text-slate-600">{cs.desc}</p>
                </div>
              ))}

              {/* Composite */}
              <div className="pt-3 border-t border-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[11px] font-bold text-slate-200">Composite Probability</p>
                  <p className="text-xl font-black font-mono text-emerald-400">{compositeScore}</p>
                </div>
                <p className="text-[9px] text-slate-500">Classified: Highly Likely Mineral Oil Slick</p>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden mt-2">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${parseFloat(compositeScore) * 100}%` }} />
                </div>
              </div>
            </div>

            {/* Processing Timeline */}
            <div className="border-t border-slate-800/60 px-4 py-3">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">⏱ Processing Pipeline Timeline</p>
              <div className="space-y-2">
                {[
                  { label: 'Varuna-SAR Ingestion & SHA-256 Registered', time: '2024-11-14 04:22 UTC (+18s)' },
                  { label: 'Lee 5×5 Speckle Filter & Calibration', time: '2024-11-14 04:23 UTC (+38s)' },
                  { label: 'U-Net Segmentation: SAR Mask Extracted', time: '2024-11-14 04:25 UTC (+2m 11s)' },
                  { label: 'Backward Lagrangian Drift (N=1000, 72h)', time: '2024-11-14 04:29 UTC (+6m 52s)' },
                  { label: 'AIS Correlation: 3 Candidates Ranked', time: '2024-11-14 04:33 UTC (+10m 59s)' },
                  { label: 'Dossier Sealed with SHA-256 Hash', time: '2024-11-14 04:34 UTC (+11m 47s)', highlight: true },
                ].map((step, i) => (
                  <div key={i}>
                    <p className={`text-[9px] font-medium ${step.highlight ? 'text-cyan-400' : 'text-slate-400'}`}>{step.label}</p>
                    <p className="text-[8px] text-slate-600 font-mono">{step.time}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
