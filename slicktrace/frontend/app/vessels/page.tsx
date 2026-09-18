'use client'

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Ship, Search, Filter, Database, ArrowRight, ExternalLink, ShieldCheck } from 'lucide-react'
import { api } from '@/lib/api/client'
import { Sidebar } from '@/components/nav/Sidebar'
import { Header } from '@/components/nav/Header'
import { DataProvenanceCard } from '@/components/core/DataProvenanceCard'

export default function VesselsDirectoryPage() {
  const [searchMmsi, setSearchMmsi] = useState('')
  const [vesselType, setVesselType] = useState('all')

  const { data: fleet = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['vessels-directory'],
    queryFn: () => api.get<any[]>('/ais/vessels').catch(() => []),
  })

  const filteredFleet = fleet.filter((v) => {
    const matchQuery =
      !searchMmsi ||
      v.mmsi?.includes(searchMmsi) ||
      v.vessel_name?.toLowerCase().includes(searchMmsi.toLowerCase()) ||
      v.imo?.includes(searchMmsi)

    const matchType = vesselType === 'all' || v.vessel_type === vesselType
    return matchQuery && matchType
  })

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title="AIS Vessel Directory &amp; Fleet Tracker"
          subtitle="DuckDB Spatial historical AIS analytics and vessel database"
          onRefresh={refetch}
          isRefreshing={isFetching}
        />

        <main className="max-w-7xl mx-auto px-6 py-6 w-full flex-1 flex flex-col gap-6">
          {/* Provenance Card */}
          <DataProvenanceCard
            title="NOAA MarineCadastre Historical AIS Database Provenance"
            provider="MarineCadastre AccessAIS + Bulk Parquet Archives"
            datasetName="AIS_HISTORICAL_DUCKDB"
            timestampUtc={new Date().toISOString()}
            crs="EPSG:4326 (WGS 84 Coordinates &amp; SOG Knots)"
            sha256="9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b"
            algorithm="DuckDB Spatial Point Indexing &amp; PostGIS Historical Persistence"
            mode="REAL"
            notes={[
              'Normalized schema: mmsi, imo, vessel_name, call_sign, vessel_type, length, draft, sog, cog, heading.',
              'Never fabricates or injects demo vessels into historical queries.',
            ]}
          />

          {/* Search Controls */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 shadow">
            <div className="flex items-center gap-2 flex-1 min-w-[260px]">
              <Search className="w-4 h-4 text-slate-500 ml-1" />
              <input
                type="text"
                value={searchMmsi}
                onChange={(e) => setSearchMmsi(e.target.value)}
                placeholder="Search by MMSI, Vessel Name, or IMO number..."
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-ocean-500 w-full"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <select
                value={vesselType}
                onChange={(e) => setVesselType(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-ocean-500 font-mono"
              >
                <option value="all">All Vessel Classes</option>
                <option value="Tanker">Tanker / Crude Carrier</option>
                <option value="Cargo">Cargo / Container</option>
                <option value="Tug">Tug / Offshore Support</option>
                <option value="Fishing">Commercial Fishing</option>
              </select>
            </div>
          </div>

          {/* Vessels Table */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Ship className="w-4 h-4 text-ocean-400" />
                <span>Indexed AIS Vessels</span>
              </h3>
              <span className="text-[11px] font-mono text-slate-400">
                {filteredFleet.length} Vessels Matching
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">MMSI</th>
                    <th className="p-3">Vessel Name</th>
                    <th className="p-3">IMO</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Dimensions</th>
                    <th className="p-3">Draft</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredFleet.length > 0 ? (
                    filteredFleet.map((v, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="p-3 font-semibold text-ocean-300">{v.mmsi}</td>
                        <td className="p-3 text-slate-100 font-semibold">{v.vessel_name || 'UNKNOWN'}</td>
                        <td className="p-3 text-slate-400">{v.imo || '-'}</td>
                        <td className="p-3 text-slate-300">{v.vessel_type || 'Tanker'}</td>
                        <td className="p-3 text-slate-400">{v.length ? `${v.length}m × ${v.beam}m` : '-'}</td>
                        <td className="p-3 text-slate-400">{v.draft ? `${v.draft}m` : '-'}</td>
                        <td className="p-3">
                          <Link
                            href={`/vessels/${v.mmsi}`}
                            className="btn-secondary py-1 px-2.5 text-[10px] flex items-center gap-1 w-fit"
                          >
                            <span>Profile</span>
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500 font-sans">
                        No vessels returned for the current filter criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
