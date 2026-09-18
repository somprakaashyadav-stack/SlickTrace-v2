'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, CheckCircle2, AlertCircle, Database, Server, Key, Satellite } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

export default function SettingsPage() {
  const { data: health } = useQuery({
    queryKey: ['health-settings'],
    queryFn: () => api.get<any>('/health'),
  })

  const sources = [
    {
      id: 'copernicus_dataspace',
      name: 'Copernicus Data Space Ecosystem (CDSE)',
      type: 'SAR & Optical Satellite Imagery',
      keyEnv: 'CDSE_USERNAME / CDSE_PASSWORD',
      docsUrl: 'https://dataspace.copernicus.eu/',
      available: !health?.unavailable_sources?.copernicus_dataspace,
      reason: health?.unavailable_sources?.copernicus_dataspace,
    },
    {
      id: 'copernicus_marine',
      name: 'Copernicus Marine Service (CMEMS)',
      type: 'Surface Ocean Currents (U/V)',
      keyEnv: 'CMEMS_USERNAME / CMEMS_PASSWORD',
      docsUrl: 'https://marine.copernicus.eu/',
      available: !health?.unavailable_sources?.copernicus_marine,
      reason: health?.unavailable_sources?.copernicus_marine,
    },
    {
      id: 'era5_cds',
      name: 'ECMWF ERA5 Climate Data Store (CDS)',
      type: '10m Surface Wind Vectors (U/V)',
      keyEnv: 'CDS_KEY / CDS_URL',
      docsUrl: 'https://cds.climate.copernicus.eu/',
      available: !health?.unavailable_sources?.era5_cds,
      reason: health?.unavailable_sources?.era5_cds,
    },
    {
      id: 'hycom_thredds',
      name: 'HYCOM Consortium THREDDS Server',
      type: 'Public Ocean Hydrodynamic Currents (Fallback)',
      keyEnv: 'None (Public Open Access)',
      docsUrl: 'https://tds.hycom.org/',
      available: true,
      reason: null,
    },
    {
      id: 'marinecadastre',
      name: 'NOAA MarineCadastre AccessAIS',
      type: 'Historical Bulk Vessel Trajectories',
      keyEnv: 'None (Direct HTTPS Bulk Ingestion)',
      docsUrl: 'https://marinecadastre.gov/ais/',
      available: true,
      reason: null,
    },
    {
      id: 'global_fishing_watch',
      name: 'Global Fishing Watch (GFW) API',
      type: 'Optional Global Vessel Position Telemetry',
      keyEnv: 'GFW_API_TOKEN',
      docsUrl: 'https://globalfishingwatch.org/',
      available: !health?.unavailable_sources?.global_fishing_watch,
      reason: health?.unavailable_sources?.global_fishing_watch,
    },
    {
      id: 'incois_stub',
      name: 'INCOIS / ESSO Adapter',
      type: 'Indian Ocean Regional Hydrodynamic Model',
      keyEnv: 'INCOIS_API_KEY (Stub Interface)',
      docsUrl: 'https://incois.gov.in/',
      available: false,
      reason: 'Stub adapter. Contact INCOIS for specialized API credentials.',
    },
  ]

  return (
    <div className="min-h-screen bg-slate-900 py-10 px-6">
      <div className="max-w-4xl mx-auto flex flex-col gap-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>

        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Server className="w-5 h-5 text-brand-400" />
            <span>Data Sources &amp; Adapter Integrations</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Status of live remote sensing, ocean physics hydrodynamic models, and historical AIS feeds.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          {sources.map((src) => (
            <div
              key={src.id}
              className="card flex flex-col md:flex-row md:items-center justify-between p-4 gap-4"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm text-slate-200">{src.name}</h3>
                  {src.available ? (
                    <span className="badge bg-emerald-950 text-emerald-400 border border-emerald-800 text-[9pt]">
                      CONNECTED / AVAILABLE
                    </span>
                  ) : (
                    <span className="badge bg-amber-950 text-amber-400 border border-amber-800 text-[9pt]">
                      UNAVAILABLE
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">{src.type}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Key className="w-3 h-3 text-slate-500" />
                  <span className="font-mono text-[10pt] text-slate-400">{src.keyEnv}</span>
                </div>
                {!src.available && src.reason && (
                  <p className="text-[10pt] text-amber-300 mt-1 italic">
                    Reason: {src.reason}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <a
                  href={src.docsUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded-lg transition-colors"
                >
                  Provider Portal
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
