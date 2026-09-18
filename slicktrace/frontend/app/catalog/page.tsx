'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  Satellite,
  Search,
  Calendar,
  Cloud,
  Layers,
  ArrowLeft,
  ExternalLink,
  Download,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  MapPin,
  ShieldAlert,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api/client'
import { Incident } from '@/lib/api/types'
import { toast } from 'sonner'
import { cn, formatBytes } from '@/lib/utils'

interface CopernicusStatus {
  provider: string
  available: boolean
  reason: string
  registration_url: string
  supported_missions: string[]
}

interface ProductItem {
  id: string
  name: string
  content_length_bytes: number
  content_date_start?: string
  content_date_end?: string
  platform?: string
  sensor?: string
  product_type?: string
  polarization?: string
  cloud_cover_percent?: number
  footprint_geojson?: any
  quicklook_url?: string
}

interface SearchResponse {
  provider_status: 'available' | 'unavailable'
  unavailable_reason?: string
  registration_url: string
  total_results: number
  products: ProductItem[]
}

export default function SatelliteCatalogPage() {
  const [platform, setPlatform] = useState<'SENTINEL-1' | 'SENTINEL-2'>('SENTINEL-1')
  const [productType, setProductType] = useState('GRD')
  const [polarization, setPolarization] = useState('VV+VH')
  const [maxCloud, setMaxCloud] = useState(20)
  const [dateFrom, setDateFrom] = useState('2023-05-01')
  const [dateTo, setDateTo] = useState('2023-05-15')

  // Bounding Box (Default: Gulf of Mexico oil transit corridor)
  const [latMin, setLatMin] = useState('27.0')
  const [latMax, setLatMax] = useState('29.0')
  const [lonMin, setLonMin] = useState('-91.5')
  const [lonMax, setLonMax] = useState('-89.0')

  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('')
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  // Fetch CDSE Status
  const { data: statusData } = useQuery({
    queryKey: ['copernicus-status'],
    queryFn: () => api.get<CopernicusStatus>('/copernicus/status'),
  })

  // Fetch Incidents for direct evidence linking
  const { data: incidents } = useQuery({
    queryKey: ['incidents-list'],
    queryFn: () => api.get<Incident[]>('/incidents'),
  })

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSearching(true)

    // Build WKT polygon from bbox
    const aoiWkt = `POLYGON((${lonMin} ${latMin}, ${lonMax} ${latMin}, ${lonMax} ${latMax}, ${lonMin} ${latMax}, ${lonMin} ${latMin}))`

    try {
      const res = await api.post<SearchResponse>('/copernicus/search', {
        platform,
        date_from: new Date(dateFrom).toISOString(),
        date_to: new Date(dateTo).toISOString(),
        aoi_wkt: aoiWkt,
        product_type: productType || undefined,
        polarization: platform === 'SENTINEL-1' ? polarization : undefined,
        max_cloud_cover: platform === 'SENTINEL-2' ? maxCloud : undefined,
        limit: 20,
      })
      setSearchResults(res)
      if (res.provider_status === 'unavailable') {
        toast.error('Copernicus Data Space provider unavailable')
      } else {
        toast.success(`Found ${res.total_results} matching real products`)
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Search request failed')
    } finally {
      setIsSearching(false)
    }
  }

  const handleDownloadAndIngest = async (productId: string) => {
    setDownloadingId(productId)
    try {
      const res = await api.post<any>('/copernicus/download', {
        product_id: productId,
        incident_id: selectedIncidentId ? selectedIncidentId : undefined,
      })
      toast.success(
        selectedIncidentId
          ? 'Scene downloaded & linked to incident as SatelliteEvidence!'
          : 'Scene downloaded and cached in MinIO!'
      )
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Download failed')
    } finally {
      setDownloadingId(null)
    }
  }

  const handlePreset = (preset: string) => {
    if (preset === 'gom') {
      setLatMin('27.0'); setLatMax('29.0'); setLonMin('-91.5'); setLonMax('-89.0')
    } else if (preset === 'north_sea') {
      setLatMin('56.0'); setLatMax('58.5'); setLonMin('2.0'); setLonMax('4.5')
    } else if (preset === 'persian_gulf') {
      setLatMin('26.0'); setLatMax('28.0'); setLonMin('51.0'); setLonMax('54.0')
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 py-8 px-6">
      <div className="max-w-7xl mx-auto flex flex-col gap-6">
        {/* Navigation & Header */}
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Live Satellite Data Service:</span>
            {statusData?.available ? (
              <span className="badge bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10pt] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> CDSE Connected
              </span>
            ) : (
              <span className="badge bg-amber-950 text-amber-400 border border-amber-800 text-[10pt] flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> CDSE Credentials Unset
              </span>
            )}
          </div>
        </div>

        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Satellite className="w-5 h-5 text-brand-400" />
            <span>Copernicus Data Space — Satellite Catalog</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Search live ESA Sentinel-1 SAR &amp; Sentinel-2 optical imagery catalogs via Copernicus Data Space Ecosystem (CDSE). Download and ingest real products as tamper-evident satellite evidence.
          </p>
        </div>

        {/* Provider Status Diagnostic Banner */}
        {statusData && !statusData.available && (
          <div className="bg-amber-950/40 border border-amber-800/80 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-amber-200 font-semibold block">
                  Copernicus Data Space API Access Unavailable
                </strong>
                <span className="text-amber-300/80">
                  {statusData.reason} In accordance with the SlickTrace Real Data Contract, synthetic scenes will never be fabricated.
                </span>
              </div>
            </div>
            <a
              href={statusData.registration_url}
              target="_blank"
              rel="noreferrer"
              className="bg-amber-700 hover:bg-amber-600 text-white font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors flex-shrink-0"
            >
              <span>Register Free Account</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        )}

        {/* Search & Query Builder Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Query Filters */}
          <form onSubmit={handleSearch} className="lg:col-span-5 card flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-700 pb-3">
              <h2 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <Search className="w-4 h-4 text-brand-400" />
                <span>Search Filters</span>
              </h2>
              <div className="flex items-center gap-1 text-[10pt]">
                <button
                  type="button"
                  onClick={() => { setPlatform('SENTINEL-1'); setProductType('GRD') }}
                  className={cn(
                    'px-2.5 py-1 rounded font-medium transition-colors',
                    platform === 'SENTINEL-1' ? 'bg-brand-600 text-white' : 'bg-slate-700 text-slate-400'
                  )}
                >
                  Sentinel-1 SAR
                </button>
                <button
                  type="button"
                  onClick={() => { setPlatform('SENTINEL-2'); setProductType('L2A') }}
                  className={cn(
                    'px-2.5 py-1 rounded font-medium transition-colors',
                    platform === 'SENTINEL-2' ? 'bg-brand-600 text-white' : 'bg-slate-700 text-slate-400'
                  )}
                >
                  Sentinel-2 Optical
                </button>
              </div>
            </div>

            {/* Spatial AOI Bounding Box */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs">
                <label className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-ocean-400" />
                  <span>Area of Interest (Bounding Coordinates)</span>
                </label>
                <div className="flex items-center gap-1 text-[9pt]">
                  <span className="text-slate-500">Presets:</span>
                  <button type="button" onClick={() => handlePreset('gom')} className="text-brand-400 hover:underline">Gulf of Mex</button>
                  <span>·</span>
                  <button type="button" onClick={() => handlePreset('north_sea')} className="text-brand-400 hover:underline">North Sea</button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[10pt] text-slate-400">Lat Min (South)</span>
                  <input
                    type="text"
                    value={latMin}
                    onChange={(e) => setLatMin(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <span className="text-[10pt] text-slate-400">Lat Max (North)</span>
                  <input
                    type="text"
                    value={latMax}
                    onChange={(e) => setLatMax(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <span className="text-[10pt] text-slate-400">Lon Min (West)</span>
                  <input
                    type="text"
                    value={lonMin}
                    onChange={(e) => setLonMin(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <span className="text-[10pt] text-slate-400">Lon Max (East)</span>
                  <input
                    type="text"
                    value={lonMax}
                    onChange={(e) => setLonMax(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-2 gap-2">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-400" />
                  <span>Date From</span>
                </label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-400" />
                  <span>Date To</span>
                </label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            {/* Mission Specific Filters */}
            {platform === 'SENTINEL-1' ? (
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-slate-300">Product Type</label>
                  <select
                    value={productType}
                    onChange={(e) => setProductType(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
                  >
                    <option value="GRD">GRD (Ground Range Detected)</option>
                    <option value="SLC">SLC (Single Look Complex)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-slate-300">Polarization</label>
                  <select
                    value={polarization}
                    onChange={(e) => setPolarization(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
                  >
                    <option value="VV+VH">VV+VH (Dual Co/Cross)</option>
                    <option value="VV">VV (Co-pol)</option>
                    <option value="VH">VH (Cross-pol)</option>
                    <option value="HH">HH</option>
                  </select>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <label className="font-semibold text-slate-300 flex items-center gap-1">
                    <Cloud className="w-3.5 h-3.5 text-ocean-400" />
                    <span>Max Cloud Cover Constraint</span>
                  </label>
                  <span className="font-mono text-ocean-300">{maxCloud}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={maxCloud}
                  onChange={(e) => setMaxCloud(parseInt(e.target.value, 10))}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-ocean-400"
                />
              </div>
            )}

            {/* Target Incident Selection for Ingestion */}
            <div className="flex flex-col gap-1 pt-1 border-t border-slate-700">
              <label className="text-xs font-semibold text-slate-300">Link Ingested Scene to Incident</label>
              <select
                value={selectedIncidentId}
                onChange={(e) => setSelectedIncidentId(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
              >
                <option value="">(Cache only — do not link to investigation)</option>
                {incidents?.map((inc) => (
                  <option key={inc.id} value={inc.id}>
                    {inc.title} ({inc.id.slice(0, 8)})
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={isSearching}
              className="btn-primary py-2.5 flex items-center justify-center gap-2 text-xs disabled:opacity-50 mt-2"
            >
              {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              <span>Search Copernicus Data Space</span>
            </button>
          </form>

          {/* Search Results Display */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <Layers className="w-4 h-4 text-ocean-400" />
                <span>Catalog Query Results</span>
              </h2>
              {searchResults && (
                <span className="text-xs text-slate-400">
                  {searchResults.total_results} scene{searchResults.total_results === 1 ? '' : 's'} found
                </span>
              )}
            </div>

            {/* Unavailable State Card */}
            {searchResults?.provider_status === 'unavailable' && (
              <div className="card border-amber-800/80 bg-amber-950/20 p-6 flex flex-col items-center justify-center text-center gap-3">
                <AlertTriangle className="w-10 h-10 text-amber-400" />
                <h3 className="font-semibold text-amber-200 text-sm">Provider Unavailable</h3>
                <p className="text-xs text-amber-300/80 max-w-md">
                  {searchResults.unavailable_reason}
                </p>
                <a
                  href={searchResults.registration_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary text-xs flex items-center gap-1.5 mt-2"
                >
                  <span>Open Copernicus Portal</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            )}

            {/* Initial Empty State */}
            {!searchResults && (
              <div className="card p-12 text-center text-slate-500 flex flex-col items-center justify-center gap-2">
                <Satellite className="w-12 h-12 text-slate-600 mb-2" />
                <p className="font-medium text-slate-300 text-sm">No Active Search Query</p>
                <p className="text-xs max-w-sm">
                  Specify an Area of Interest (AOI), date window, and sensor constraints to query the live Copernicus satellite catalog.
                </p>
              </div>
            )}

            {/* Results List */}
            {searchResults?.provider_status === 'available' && searchResults.products.length === 0 && (
              <div className="card p-8 text-center text-slate-400">
                <p className="font-medium">No Matching Satellite Scenes Found</p>
                <p className="text-xs text-slate-500 mt-1">
                  Try expanding the bounding box coordinates or broadening the temporal window.
                </p>
              </div>
            )}

            {searchResults?.provider_status === 'available' && searchResults.products.length > 0 && (
              <div className="flex flex-col gap-3">
                {searchResults.products.map((p) => (
                  <div key={p.id} className="card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-brand-500 transition-colors">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-slate-200">{p.name}</span>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-[10pt] text-slate-400">
                        <span className="badge bg-slate-700 text-slate-300">{p.platform} ({p.sensor})</span>
                        <span className="badge bg-slate-800 text-slate-400 border border-slate-700">{p.product_type}</span>
                        {p.polarization && (
                          <span className="badge bg-ocean-950 text-ocean-300 border border-ocean-800 font-mono">{p.polarization}</span>
                        )}
                        {p.cloud_cover_percent != null && (
                          <span className="badge bg-sky-950 text-sky-300 border border-sky-800">
                            Cloud: {p.cloud_cover_percent.toFixed(1)}%
                          </span>
                        )}
                        <span>·</span>
                        <span>{formatBytes(p.content_length_bytes)}</span>
                      </div>
                      <div className="text-[10pt] text-slate-500 font-mono mt-0.5">
                        Acquired: {p.content_date_start ? new Date(p.content_date_start).toUTCString() : 'N/A'}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => handleDownloadAndIngest(p.id)}
                        disabled={downloadingId === p.id}
                        className="btn-primary text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
                      >
                        {downloadingId === p.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Download className="w-3.5 h-3.5" />
                        )}
                        <span>{selectedIncidentId ? 'Ingest into Incident' : 'Download & Cache'}</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
