import * as React from 'react'
import { Eye, EyeOff } from 'lucide-react'

export interface MapLayer {
  id: string
  label: string
  visible: boolean
  count?: number
  color?: string
}

export interface LayerControlProps {
  layers: MapLayer[]
  onToggleLayer: (id: string) => void
  onClose?: () => void
}

export function LayerControl({ layers, onToggleLayer }: LayerControlProps) {
  return (
    <div className="bg-slate-950/95 p-3 rounded-xl border border-slate-800/80 shadow-2xl backdrop-blur-md w-56 text-xs space-y-2">
      <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
          Layer Visibility
        </span>
        <span className="text-[10px] font-mono text-sky-400">
          {layers.filter((l) => l.visible).length}/{layers.length}
        </span>
      </div>
      <div className="space-y-1">
        {layers.map((layer) => (
          <button
            key={layer.id}
            onClick={() => onToggleLayer(layer.id)}
            className={`w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-left transition-all ${
              layer.visible
                ? 'bg-slate-900/90 text-slate-100 hover:bg-slate-850'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <div className="flex items-center space-x-2 truncate">
              {layer.color && (
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: layer.color }}
                />
              )}
              <span className="text-xs truncate">{layer.label}</span>
            </div>
            <div className="shrink-0 text-slate-400 ml-2">
              {layer.visible ? (
                <Eye className="w-3.5 h-3.5 text-sky-400" />
              ) : (
                <EyeOff className="w-3.5 h-3.5 opacity-40" />
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
