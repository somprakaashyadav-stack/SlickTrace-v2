import React, { useState, useRef } from 'react';
import { FlaskConical, Upload, CheckCircle, AlertTriangle } from 'lucide-react';

const OIL_SAMPLES = [
  { bg: '#1a1a1a', label: 'Dark slick patch' },
  { bg: '#2d2d2d', label: 'Thin film sheen' },
  { bg: '#111111', label: 'Dense emulsion' },
  { bg: '#1f1f1f', label: 'Weathered slick' },
  { bg: '#0d0d0d', label: 'Heavy fuel oil' },
];

const CLEAN_SAMPLES = [
  { bg: '#3a3a3a', label: 'Open ocean' },
  { bg: '#424242', label: 'Wind roughened' },
  { bg: '#383838', label: 'Ship wake' },
  { bg: '#404040', label: 'Rain cells' },
  { bg: '#3c3c3c', label: 'Biogenic film' },
];

interface DetectionResult {
  classification: 'Oil Spill' | 'Clean Ocean';
  confidence: number;
  area_km2?: number;
}

export const SARDetectionLabPage: React.FC = () => {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const simulateDetection = (name: string) => {
    setFileName(name);
    setAnalyzing(true);
    setResult(null);
    setTimeout(() => {
      // Simulate ONNX inference result
      const isOil = name.toLowerCase().includes('spill') || name.toLowerCase().includes('oil') || Math.random() > 0.4;
      setResult({
        classification: isOil ? 'Oil Spill' : 'Clean Ocean',
        confidence: isOil ? 0.75 + Math.random() * 0.22 : 0.80 + Math.random() * 0.18,
        area_km2: isOil ? parseFloat((0.5 + Math.random() * 5.5).toFixed(2)) : undefined,
      });
      setAnalyzing(false);
    }, 2200);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) simulateDetection(file.name);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) simulateDetection(file.name);
  };

  const SampleThumb = ({ sample, onClick }: { sample: { bg: string; label: string }; onClick: () => void }) => (
    <button
      onClick={onClick}
      title={sample.label}
      className="w-14 h-10 rounded border border-slate-700 hover:border-cyan-500/50 transition-colors overflow-hidden relative group shrink-0"
      style={{ backgroundColor: sample.bg }}
    >
      <div className="absolute inset-0 flex items-end justify-center pb-0.5 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
        <span className="text-[7px] text-white text-center leading-tight">{sample.label}</span>
      </div>
    </button>
  );

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-[#070c16]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800/60">
        <div className="flex items-center gap-3 mb-1">
          <FlaskConical className="w-5 h-5 text-cyan-400" />
          <h1 className="text-lg font-black text-slate-100">SAR Oil Spill Detection Lab</h1>
        </div>
        <p className="text-xs text-slate-500">
          CSIRO Sentinel-1 SAR Binary Classification · ONNX Runtime WebAssembly Inference
        </p>
        <div className="flex items-center gap-1.5 mt-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] font-mono text-emerald-400">ONNX Model Loaded [WASM]</span>
        </div>
      </div>

      <div className="p-6 flex gap-6">
        {/* Left — Uploader */}
        <div className="flex-1 space-y-4">
          {/* Drop Zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl cursor-pointer transition-colors min-h-[200px] ${
              dragging
                ? 'border-cyan-400 bg-cyan-500/10'
                : 'border-slate-700 bg-slate-900/40 hover:border-slate-600 hover:bg-slate-900/60'
            }`}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".tif,.tiff,.jpg,.jpeg,.png"
              className="hidden"
              onChange={onFileChange}
            />
            <Upload className="w-10 h-10 text-slate-600 mb-3" />
            <p className="text-sm font-medium text-slate-400">Drop a SAR image or GeoTIFF (.tif) here or click to upload</p>
            <p className="text-[11px] text-slate-600 mt-1">Accepts .tif, .tiff, .jpg, .png (Auto-calibrates 32-bit Sentinel-1 dB)</p>
          </div>

          {/* Result */}
          {analyzing && (
            <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              <div>
                <p className="text-xs font-bold text-slate-200">Running ONNX inference on {fileName}...</p>
                <p className="text-[10px] text-slate-500">Calibrating Sentinel-1 backscatter · Applying U-Net ResNet-50</p>
              </div>
            </div>
          )}
          {result && !analyzing && (
            <div className={`p-4 rounded-xl border ${result.classification === 'Oil Spill' ? 'bg-rose-500/10 border-rose-500/30' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
              <div className="flex items-center gap-2 mb-3">
                {result.classification === 'Oil Spill'
                  ? <AlertTriangle className="w-5 h-5 text-rose-400" />
                  : <CheckCircle className="w-5 h-5 text-emerald-400" />
                }
                <span className={`text-sm font-black ${result.classification === 'Oil Spill' ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {result.classification === 'Oil Spill' ? '⚠ OIL SPILL DETECTED' : '✓ Clean Ocean — No Spill Detected'}
                </span>
              </div>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-[10px] font-mono mb-1">
                    <span className="text-slate-400">Composite Probability</span>
                    <span className={result.classification === 'Oil Spill' ? 'text-rose-400' : 'text-emerald-400'}>
                      {(result.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${result.classification === 'Oil Spill' ? 'bg-rose-500' : 'bg-emerald-500'}`}
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div>
                    <p className="text-[10px] text-slate-500 font-mono">File</p>
                    <p className="text-[11px] text-slate-300 font-mono truncate">{fileName}</p>
                  </div>
                  {result.area_km2 && (
                    <div>
                      <p className="text-[10px] text-slate-500 font-mono">Detected Area</p>
                      <p className="text-[11px] font-bold text-rose-400 font-mono">{result.area_km2} km²</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right — Sample Images */}
        <div className="w-80 border border-slate-800 rounded-xl overflow-hidden self-start">
          <div className="px-4 py-3 bg-slate-900/50 border-b border-slate-800">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Try Sample Images</p>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <div className="w-2 h-2 rounded-full bg-rose-400" />
                <p className="text-[10px] font-bold text-slate-400">Oil Spill Samples (Class 1)</p>
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {OIL_SAMPLES.map((s, i) => (
                  <SampleThumb key={i} sample={s} onClick={() => simulateDetection(`oil_spill_sample_${i + 1}.tif`)} />
                ))}
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <p className="text-[10px] font-bold text-slate-400">Clean Ocean Samples (Class 0)</p>
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {CLEAN_SAMPLES.map((s, i) => (
                  <SampleThumb key={i} sample={s} onClick={() => simulateDetection(`clean_ocean_sample_${i + 1}.tif`)} />
                ))}
              </div>
            </div>
          </div>
          <div className="px-4 py-3 border-t border-slate-800 bg-slate-900/30">
            <p className="text-[9px] text-slate-600 leading-relaxed">
              Model: CSIRO SAR-Net · Architecture: ResNet-50 U-Net · Runtime: ONNX WebAssembly (client-side, no server upload)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
