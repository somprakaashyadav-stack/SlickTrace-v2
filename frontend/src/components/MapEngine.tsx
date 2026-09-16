import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, CircleMarker, Polyline, Tooltip, LayersControl, LayerGroup, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import { SpillSummary, DriftSimulation, AISVesselTrack, PhysicsVerificationResponse } from '../types';

interface MapEngineProps {
  spill?: SpillSummary;
  drift?: DriftSimulation;
  vessels: AISVesselTrack[];
  physics?: PhysicsVerificationResponse;
  currentTime: number; // 0 to 100 percentage
  selectedMmsi: number | null;
  setSelectedMmsi: (mmsi: number) => void;
}

// Fix Leaflet default icon issues
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons
const createCustomIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-icon',
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6]
  });
};

const MapController: React.FC<{ selectedPos: [number, number] | null }> = ({ selectedPos }) => {
  const map = useMap();
  useEffect(() => {
    if (selectedPos) {
      map.flyTo(selectedPos, 12, { duration: 1.5 });
    }
  }, [selectedPos, map]);
  return null;
};

export const MapEngine: React.FC<MapEngineProps> = ({
  spill,
  drift,
  vessels,
  physics,
  currentTime,
  selectedMmsi,
  setSelectedMmsi
}) => {
  const defaultCenter: [number, number] = [18.9, 72.3]; // Offshore Mumbai
  const center: [number, number] = spill ? [spill.center_lat, spill.center_lon] : defaultCenter;

  // Calculate polygon coordinates (mocked as a circle around center for demo if no real polygon)
  const polygonCoords = useMemo(() => {
    if (!spill) return [];
    // Generate a simple octagon around the center
    const radius = 0.05;
    return Array.from({length: 8}).map((_, i) => {
      const angle = (i * Math.PI) / 4;
      return [
        spill.center_lat + Math.sin(angle) * radius * (1 + (i%2)*0.2),
        spill.center_lon + Math.cos(angle) * radius * (1 + (i%2)*0.2)
      ] as [number, number];
    });
  }, [spill]);

  // Determine current active particles based on timeline
  const activeParticles = useMemo(() => {
    if (!drift || !drift.trajectories) return [];
    // Calculate which step to show based on 0-100% (assuming max steps = duration)
    // Timeline maps 0 to the start of backward drift, 100 to NOW.
    // So step = currentTime / 100 * total_steps
    const maxStep = Math.max(...drift.trajectories[0].map(t => t.step));
    const currentStep = Math.floor((1 - (currentTime / 100)) * maxStep); // Drift is backward, so 100% (NOW) = step 0
    
    return drift.trajectories.map(traj => {
      const point = traj.find(p => p.step === currentStep) || traj[0];
      return [point.lat, point.lon] as [number, number];
    });
  }, [drift, currentTime]);

  const selectedVesselPos = useMemo(() => {
    if (!selectedMmsi || vessels.length === 0) return null;
    const vessel = vessels.find(v => v.mmsi === selectedMmsi);
    if (!vessel || vessel.path.length === 0) return null;
    
    const pointIdx = Math.floor((currentTime / 100) * (vessel.path.length - 1));
    const currentPos = vessel.path[pointIdx] || vessel.path[vessel.path.length - 1];
    return [currentPos.lat, currentPos.lon] as [number, number];
  }, [selectedMmsi, vessels, currentTime]);

  return (
    <div className="w-full h-full relative z-0">
      <MapContainer 
        center={center} 
        zoom={10} 
        style={{ height: '100%', width: '100%', background: '#0a192f' }}
        zoomControl={false}
      >
        <MapController selectedPos={selectedVesselPos} />
        <LayersControl position="topright">
          {/* Base Maps */}
          <LayersControl.BaseLayer checked name="Satellite Hybrid">
            <TileLayer
              url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
              attribution="&copy; Google Maps"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Standard Map">
            <TileLayer
              url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
              attribution="&copy; Google Maps"
            />
          </LayersControl.BaseLayer>

          {/* Overlays */}
          <LayersControl.Overlay checked name="Detected Spill Polygon">
            {polygonCoords.length > 0 && (
              <Polygon 
                positions={polygonCoords} 
                pathOptions={{ color: '#0ea5e9', fillColor: '#0ea5e9', fillOpacity: 0.4, weight: 2 }}
              >
                <Tooltip>Detected Oil Slick ({spill?.area_sq_km} km²)</Tooltip>
              </Polygon>
            )}
          </LayersControl.Overlay>

          <LayersControl.Overlay checked name="Origin Uncertainty Cone">
            {drift?.origin_candidate && (
              <CircleMarker
                center={[drift.origin_candidate.Y0, drift.origin_candidate.X0]}
                radius={40}
                pathOptions={{ color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.2, weight: 1, dashArray: '4, 4' }}
              >
                <Tooltip>Estimated Origin Zone</Tooltip>
              </CircleMarker>
            )}
          </LayersControl.Overlay>

          <LayersControl.Overlay checked name="Backward Particles">
            <LayerGroup>
              {activeParticles.map((pos, idx) => (
                <CircleMarker 
                  key={`bp-${idx}`} 
                  center={pos} 
                  radius={2} 
                  pathOptions={{ color: '#f43f5e', fillOpacity: 1, stroke: false }} 
                />
              ))}
            </LayerGroup>
          </LayersControl.Overlay>

          <LayersControl.Overlay checked name="AIS Tracks">
            <LayerGroup>
              {vessels.map(vessel => {
                const positions = vessel.path.map(p => [p.lat, p.lon] as [number, number]);
                const isSelected = selectedMmsi === vessel.mmsi;
                
                // Animate position based on time
                // For simplicity, we just show the whole track and a marker at the "current" position
                // Assuming timeline 0 = T-24h, 100 = NOW.
                // We map this to the array of points (rough approximation for demo)
                const pointIdx = Math.floor((currentTime / 100) * (positions.length - 1));
                const currentPos = positions[pointIdx] || positions[positions.length - 1];

                return (
                  <React.Fragment key={vessel.mmsi}>
                    <Polyline 
                      positions={positions} 
                      pathOptions={{ 
                        color: isSelected ? '#10b981' : '#64748b', 
                        weight: isSelected ? 3 : 1,
                        opacity: isSelected ? 0.8 : 0.3 
                      }} 
                    />
                    <Marker 
                      position={currentPos} 
                      icon={createCustomIcon(isSelected ? '#10b981' : '#cbd5e1')}
                      eventHandlers={{
                        click: () => setSelectedMmsi(vessel.mmsi)
                      }}
                    >
                      <Tooltip>
                        <div className="font-mono text-xs">
                          <strong>{vessel.vessel_name}</strong><br/>
                          MMSI: {vessel.mmsi}<br/>
                          Type: {vessel.vessel_type}
                        </div>
                      </Tooltip>
                    </Marker>
                  </React.Fragment>
                );
              })}
            </LayerGroup>
          </LayersControl.Overlay>
        </LayersControl>
      </MapContainer>

      {/* Map Overlay Controls / Legend */}
      <div className="absolute bottom-6 left-6 z-[1000] bg-navy-900/90 backdrop-blur border border-slate-800 rounded-lg p-3 font-mono text-[10px] space-y-2 pointer-events-none">
        <h4 className="font-bold text-slate-300 border-b border-slate-800 pb-1 mb-2">TACTICAL LEGEND</h4>
        <div className="flex items-center gap-2 text-slate-400">
          <div className="w-3 h-3 bg-sky-500/40 border border-sky-500"></div>
          <span>Satellite Detection</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <div className="w-3 h-3 rounded-full bg-rose-500"></div>
          <span>Backward Particles</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <div className="w-3 h-3 rounded-full border-2 border-amber-500 border-dashed"></div>
          <span>Origin Uncertainty</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400 mt-2 pt-2 border-t border-slate-800">
          <div className="w-3 h-3 rounded-full bg-emerald-500 border border-white"></div>
          <span className="text-emerald-400">Selected Candidate</span>
        </div>
      </div>
    </div>
  );
};
