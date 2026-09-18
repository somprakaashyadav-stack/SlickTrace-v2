import * as React from 'react'

export interface LegendItem {
  color: string
  label: string
  type: 'line' | 'fill' | 'dot' | 'polygon'
}

export function MapLegend({ items }: { items?: LegendItem[] }) {
  const defaultItems: LegendItem[] = [
    { color: '#ef4444', label: 'Spill Geometry (UTM)', type: 'polygon' },
    { color: '#f59e0b', label: 'Backward Hindcast Particles', type: 'dot' },
    { color: '#0ea5e9', label: 'Origin Probability (P90/P50)', type: 'fill' },
    { color: '#10b981', label: 'AIS Historical Trajectory', type: 'line' },
    { color: '#a855f7', label: 'Counterfactual Forward Advection', type: 'line' },
  ]

  const legendList = items || defaultItems

  return (
    <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800/80 shadow-2xl backdrop-blur-md max-w-xs text-[11px] font-mono space-y-2">
      <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 border-b border-slate-800/80 pb-1">
        Geospatial Legend
      </div>
      <div className="space-y-1.5">
        {legendList.map((item, idx) => (
          <div key={idx} className="flex items-center space-x-2">
            {item.type === 'line' && (
              <span
                className="w-4 h-0.5 rounded-full shrink-0"
                style={{ backgroundColor: item.color }}
              />
            )}
            {item.type === 'dot' && (
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: item.color }}
              />
            )}
            {item.type === 'polygon' && (
              <span
                className="w-3 h-3 rounded-sm shrink-0 border border-current opacity-80"
                style={{ backgroundColor: item.color, borderColor: item.color }}
              />
            )}
            {item.type === 'fill' && (
              <span
                className="w-3 h-3 rounded-full shrink-0 opacity-60"
                style={{ backgroundColor: item.color }}
              />
            )}
            <span className="text-slate-300 truncate">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
