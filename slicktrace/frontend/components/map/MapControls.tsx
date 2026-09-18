import * as React from 'react'
import { Plus, Minus, Compass, Maximize2, Layers } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Tooltip } from '@/components/ui/Tooltip'

export interface MapControlsProps {
  onZoomIn?: () => void
  onZoomOut?: () => void
  onResetNorth?: () => void
  onToggleFullscreen?: () => void
  onToggleLayers?: () => void
  layersOpen?: boolean
}

export function MapControls({
  onZoomIn,
  onZoomOut,
  onResetNorth,
  onToggleFullscreen,
  onToggleLayers,
  layersOpen,
}: MapControlsProps) {
  return (
    <div className="flex flex-col space-y-1.5 bg-slate-950/90 p-1 rounded-xl border border-slate-800/80 shadow-2xl backdrop-blur-md">
      {onZoomIn && (
        <Tooltip content="Zoom In" position="left">
          <Button
            variant="ghost"
            size="icon"
            onClick={onZoomIn}
            aria-label="Zoom In"
            className="w-7 h-7 text-slate-300 hover:text-white"
          >
            <Plus className="w-4 h-4" />
          </Button>
        </Tooltip>
      )}
      {onZoomOut && (
        <Tooltip content="Zoom Out" position="left">
          <Button
            variant="ghost"
            size="icon"
            onClick={onZoomOut}
            aria-label="Zoom Out"
            className="w-7 h-7 text-slate-300 hover:text-white"
          >
            <Minus className="w-4 h-4" />
          </Button>
        </Tooltip>
      )}
      {onResetNorth && (
        <Tooltip content="Reset North Orientation" position="left">
          <Button
            variant="ghost"
            size="icon"
            onClick={onResetNorth}
            aria-label="Reset North"
            className="w-7 h-7 text-slate-300 hover:text-white"
          >
            <Compass className="w-4 h-4" />
          </Button>
        </Tooltip>
      )}
      {onToggleLayers && (
        <Tooltip content="Toggle Geospatial Layers" position="left">
          <Button
            variant={layersOpen ? 'secondary' : 'ghost'}
            size="icon"
            onClick={onToggleLayers}
            aria-label="Toggle Layers"
            className={`w-7 h-7 ${layersOpen ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white'}`}
          >
            <Layers className="w-4 h-4" />
          </Button>
        </Tooltip>
      )}
      {onToggleFullscreen && (
        <Tooltip content="Expand Map View" position="left">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleFullscreen}
            aria-label="Fullscreen"
            className="w-7 h-7 text-slate-300 hover:text-white"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </Tooltip>
      )}
    </div>
  )
}
