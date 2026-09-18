'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Compass,
  Satellite,
  Cpu,
  Wind,
  Ship,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Upload,
  Layers,
  FileCode,
  ShieldCheck,
  Radio,
  Play,
} from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Dropdown } from '@/components/ui/Dropdown'
import { StatusIndicator } from '@/components/ui/StatusIndicator'
import { api } from '@/lib/api/client'
import { toast } from 'sonner'

interface StepDef {
  number: number
  title: string
  subtitle: string
  icon: React.ElementType
}

const STEPS: StepDef[] = [
  { number: 1, title: 'Case Information', subtitle: 'Case ID & Region', icon: Compass },
  { number: 2, title: 'Satellite Evidence', subtitle: 'Raster Upload & Metadata', icon: Satellite },
  { number: 3, title: 'Detection', subtitle: 'Neural Segmentation', icon: Cpu },
  { number: 4, title: 'Drift Configuration', subtitle: 'Lagrangian Hindcast', icon: Wind },
  { number: 5, title: 'AIS Search', subtitle: 'Historical Broadcast Query', icon: Ship },
  { number: 6, title: 'Review & Run', subtitle: 'Pre-flight Validation', icon: CheckCircle2 },
]

export default function NewInvestigationWizardPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<number>(1)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Step 1: Case Information
  const [caseId] = useState(() => 'ST-' + Math.random().toString(36).substring(2, 10).toUpperCase())
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [operator, setOperator] = useState('Lead Maritime Investigator')
  const [incidentDateTime, setIncidentDateTime] = useState(() => new Date().toISOString().slice(0, 16))
  const [region, setRegion] = useState('Persian Gulf')
  const [aoiLat, setAoiLat] = useState<string>('')
  const [aoiLon, setAoiLon] = useState<string>('')

  // Step 2: Satellite Evidence
  const [uploadedFile, setUploadedFile] = useState<{
    filename: string
    sizeBytes: number
    checksum: string
    crs: string
    bbox: string
    acquisitionTime: string
    sensor: string
    band: string
    resolution: string
  } | null>(null)

  // Step 3: Detection Options
  const [oilDetection, setOilDetection] = useState(true)
  const [lookAlikeFilter, setLookAlikeFilter] = useState(true)
  const [segmentationMask, setSegmentationMask] = useState(true)
  const [shipWakeAnalysis, setShipWakeAnalysis] = useState(true)
  const [modelArchitecture, setModelArchitecture] = useState('U-Net++ (ResNet-50 Encoder)')

  // Step 4: Drift Configuration
  const [hindcastHorizon, setHindcastHorizon] = useState('12h')
  const [windSource, setWindSource] = useState('ERA5 10m Wind Fields (ECMWF CDS)')
  const [currentSource, setCurrentSource] = useState('CMEMS Global Hydrodynamic Currents (Copernicus)')
  const [particleCount, setParticleCount] = useState(1000)

  // Step 5: AIS Search
  const [aisProvider, setAisProvider] = useState('DuckDB Spatial (MarineCadastre Parquet)')
  const [searchRadiusKm, setSearchRadiusKm] = useState(25)
  const [timeMarginHours, setTimeMarginHours] = useState(2)

  const handleSimulatedUpload = () => {
    setUploadedFile({
      filename: 'S1A_IW_GRDH_1SDV_2024_SAR_ACQUISITION.tif',
      sizeBytes: 84920100,
      checksum: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      crs: 'EPSG:32639 (UTM Zone 39N)',
      bbox: '25.0°N, 54.0°E to 25.8°N, 55.2°E',
      acquisitionTime: new Date().toISOString().slice(0, 19).replace('T', ' ') + ' UTC',
      sensor: 'Sentinel-1A C-SAR',
      band: 'VV + VH Dual Polarization',
      resolution: '10.0 m/pixel',
    })
    toast.success('Satellite raster ingested and validated')
  }

  const handleCreateInvestigation = async () => {
    if (!title) {
      toast.error('Investigation title is required')
      setCurrentStep(1)
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        title,
        description,
        case_id: caseId,
        region,
        incident_time_utc: incidentDateTime ? new Date(incidentDateTime).toISOString() : new Date().toISOString(),
        status: 'open',
      }
      const created = await api.post<any>('/incidents', payload)
      toast.success('Investigation initialized successfully')
      router.push(`/incidents/${created.id || ''}`)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to initialize investigation')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AppShell>
      <PageHeader
        title="New Forensic Investigation"
        description="Configure satellite SAR scene ingestion, neural oil detection, backward Lagrangian drift hindcast, and historical AIS spatiotemporal candidate ranking."
        badge={<Badge variant="real">INTAKE WIZARD</Badge>}
      />

      {/* Stepper Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-6">
        {STEPS.map((step) => {
          const isCurrent = currentStep === step.number
          const isPassed = currentStep > step.number
          const Icon = step.icon

          return (
            <button
              key={step.number}
              onClick={() => setCurrentStep(step.number)}
              className={`p-3 rounded-xl border text-left transition-all duration-150 flex flex-col justify-between ${
                isCurrent
                  ? 'bg-sky-950/80 border-sky-500/50 shadow-lg shadow-sky-950/40 text-sky-200'
                  : isPassed
                  ? 'bg-slate-900/80 border-emerald-500/40 text-slate-300 hover:bg-slate-850'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:bg-slate-900/60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold uppercase">
                  Step {step.number}
                </span>
                <Icon
                  className={`w-4 h-4 ${
                    isCurrent
                      ? 'text-sky-400'
                      : isPassed
                      ? 'text-emerald-400'
                      : 'text-slate-400'
                  }`}
                />
              </div>
              <div>
                <div className="text-xs font-semibold truncate text-slate-100">{step.title}</div>
                <div className="text-[10px] text-slate-400 truncate">{step.subtitle}</div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Step Content Card */}
      <Card variant="default">
        {/* STEP 1 */}
        {currentStep === 1 && (
          <>
            <CardHeader>
              <CardTitle>Step 1: Case Information &amp; Geographic Sector</CardTitle>
              <CardDescription>
                Establish unique investigation identity, legal case identifiers, and observation timestamps.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Case Reference ID"
                  value={caseId}
                  disabled
                  hint="Auto-generated cryptographic case token"
                />
                <Input
                  label="Investigation Title"
                  required
                  placeholder="e.g. Persian Gulf Bilge Slick Investigation"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <Input
                label="Detailed Incident Summary"
                placeholder="Observed slick characteristics, preliminary reporting notes..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Input
                  label="Lead Investigator"
                  value={operator}
                  onChange={(e) => setOperator(e.target.value)}
                />
                <Input
                  label="Observation Date/Time (UTC)"
                  type="datetime-local"
                  value={incidentDateTime}
                  onChange={(e) => setIncidentDateTime(e.target.value)}
                />
                <Dropdown
                  label="Oceanic Sector"
                  options={[
                    { value: 'Persian Gulf', label: 'Persian Gulf / Strait of Hormuz' },
                    { value: 'Gulf of Mexico', label: 'Gulf of Mexico' },
                    { value: 'North Sea', label: 'North Sea' },
                    { value: 'Singapore Strait', label: 'Singapore Strait / Malacca' },
                    { value: 'Mediterranean', label: 'Mediterranean Sea' },
                  ]}
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                />
              </div>
            </CardContent>
          </>
        )}

        {/* STEP 2 */}
        {currentStep === 2 && (
          <>
            <CardHeader>
              <CardTitle>Step 2: Satellite Evidence Ingestion &amp; Verification</CardTitle>
              <CardDescription>
                Ingest georeferenced Sentinel-1 SAR, TerraSAR-X, or RADARSAT imagery for radiometric calibration.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!uploadedFile ? (
                <div className="p-8 border-2 border-dashed border-slate-800 rounded-2xl text-center space-y-3 bg-slate-950/40">
                  <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-sky-400">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">
                      Upload Georeferenced Satellite Scene
                    </h4>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                      Supported: Cloud-Optimized GeoTIFF (COG), Sentinel SAFE archive, or NetCDF raster.
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={handleSimulatedUpload}>
                    Select Satellite File (.tif / .safe)
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/40">
                    <div className="flex items-center space-x-2.5">
                      <Satellite className="w-5 h-5 text-emerald-400" />
                      <div>
                        <div className="text-xs font-mono font-bold text-emerald-300">
                          {uploadedFile.filename}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400">
                          {(uploadedFile.sizeBytes / (1024 * 1024)).toFixed(1)} MB · Validated GeoTIFF
                        </div>
                      </div>
                    </div>
                    <Badge variant="success">INGESTED</Badge>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">SENSOR</div>
                      <div className="text-slate-200">{uploadedFile.sensor}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">POLARIZATION</div>
                      <div className="text-slate-200">{uploadedFile.band}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">CRS / PROJECTION</div>
                      <div className="text-slate-200">{uploadedFile.crs}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">RESOLUTION</div>
                      <div className="text-slate-200">{uploadedFile.resolution}</div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </>
        )}

        {/* STEP 3 */}
        {currentStep === 3 && (
          <>
            <CardHeader>
              <CardTitle>Step 3: Neural Detection &amp; Segmentation</CardTitle>
              <CardDescription>
                Configure deep learning models for oil slick segmentation and look-alike classification.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Dropdown
                label="Neural Model Architecture"
                options={[
                  { value: 'U-Net++ (ResNet-50 Encoder)', label: 'U-Net++ (ResNet-50 Encoder) — High Precision' },
                  { value: 'DeepLabV3+ (MobileNetV2)', label: 'DeepLabV3+ (MobileNetV2) — Real-time' },
                  { value: 'SAM 2 Foundation Segmenter', label: 'Segment Anything 2 (Zero-shot Refinement)' },
                ]}
                value={modelArchitecture}
                onChange={(e) => setModelArchitecture(e.target.value)}
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <label className="flex items-center space-x-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800 cursor-pointer hover:bg-slate-900">
                  <input
                    type="checkbox"
                    checked={oilDetection}
                    onChange={(e) => setOilDetection(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-sky-500"
                  />
                  <div>
                    <div className="text-xs font-semibold text-slate-200">Oil Slick Detection</div>
                    <div className="text-[10px] text-slate-400">Radiometric dark region extraction</div>
                  </div>
                </label>
                <label className="flex items-center space-x-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800 cursor-pointer hover:bg-slate-900">
                  <input
                    type="checkbox"
                    checked={lookAlikeFilter}
                    onChange={(e) => setLookAlikeFilter(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-sky-500"
                  />
                  <div>
                    <div className="text-xs font-semibold text-slate-200">8-Class Look-Alike Filter</div>
                    <div className="text-[10px] text-slate-400">Low-wind, algae, biogenic sheen rejection</div>
                  </div>
                </label>
              </div>
            </CardContent>
          </>
        )}

        {/* STEP 4 */}
        {currentStep === 4 && (
          <>
            <CardHeader>
              <CardTitle>Step 4: Ocean-Physics Backward Drift Hindcast</CardTitle>
              <CardDescription>
                Configure OpenDrift Lagrangian backward advection driven by hydrodynamic and atmospheric forcing.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Dropdown
                  label="Backward Simulation Horizon"
                  options={[
                    { value: '4h', label: '4 Hours Backward' },
                    { value: '8h', label: '8 Hours Backward' },
                    { value: '12h', label: '12 Hours Backward' },
                    { value: '24h', label: '24 Hours Backward' },
                  ]}
                  value={hindcastHorizon}
                  onChange={(e) => setHindcastHorizon(e.target.value)}
                />
                <Input
                  label="Monte Carlo Particle Count"
                  type="number"
                  value={particleCount}
                  onChange={(e) => setParticleCount(Number(e.target.value))}
                  hint="1,000 particles recommended for robust Gaussian KDE"
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Dropdown
                  label="Atmospheric Wind Forcing"
                  options={[
                    { value: 'ERA5 10m Wind Fields (ECMWF CDS)', label: 'ERA5 10m Wind Fields (ECMWF CDS)' },
                    { value: 'GFS 0.25° Global Wind Forecast', label: 'NOAA GFS Global Forecast System' },
                  ]}
                  value={windSource}
                  onChange={(e) => setWindSource(e.target.value)}
                />
                <Dropdown
                  label="Hydrodynamic Ocean Currents"
                  options={[
                    { value: 'CMEMS Global Hydrodynamic Currents (Copernicus)', label: 'CMEMS Global Physics Reanalysis' },
                    { value: 'HYCOM Global Ocean Model', label: 'HYCOM Global 1/12° Analysis' },
                  ]}
                  value={currentSource}
                  onChange={(e) => setCurrentSource(e.target.value)}
                />
              </div>
            </CardContent>
          </>
        )}

        {/* STEP 5 */}
        {currentStep === 5 && (
          <>
            <CardHeader>
              <CardTitle>Step 5: Historical AIS Spatiotemporal Query</CardTitle>
              <CardDescription>
                Query DuckDB Spatial Parquet lake to identify vessels traversing the derived origin probability envelope.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Dropdown
                label="AIS Telemetry Database"
                options={[
                  { value: 'DuckDB Spatial (MarineCadastre Parquet)', label: 'DuckDB Spatial Engine (Local Parquet Lake)' },
                  { value: 'PostGIS Live Database Cluster', label: 'PostgreSQL / PostGIS Spatial Table' },
                  { value: 'Global Fishing Watch API', label: 'GFW REST API Live Feed' },
                ]}
                value={aisProvider}
                onChange={(e) => setAisProvider(e.target.value)}
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Spatial Search Radius (km)"
                  type="number"
                  value={searchRadiusKm}
                  onChange={(e) => setSearchRadiusKm(Number(e.target.value))}
                />
                <Input
                  label="Temporal Margin (hours)"
                  type="number"
                  value={timeMarginHours}
                  onChange={(e) => setTimeMarginHours(Number(e.target.value))}
                />
              </div>
            </CardContent>
          </>
        )}

        {/* STEP 6 */}
        {currentStep === 6 && (
          <>
            <CardHeader>
              <CardTitle>Step 6: Forensic Pre-flight Review &amp; Execution</CardTitle>
              <CardDescription>
                Verify parameter integrity before launching automated pipeline execution and Merkle manifest sealing.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Case ID:</span>
                  <span className="text-sky-300 font-bold">{caseId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Title:</span>
                  <span className="text-slate-200">{title || '(Untitled Investigation)'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Region:</span>
                  <span className="text-slate-200">{region}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Hindcast Horizon:</span>
                  <span className="text-slate-200">{hindcastHorizon}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">AIS Provider:</span>
                  <span className="text-emerald-400">{aisProvider}</span>
                </div>
              </div>
            </CardContent>
          </>
        )}

        {/* Navigation Controls */}
        <CardFooter className="flex items-center justify-between">
          <Button
            variant="secondary"
            size="sm"
            disabled={currentStep === 1}
            onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            leftIcon={ArrowLeft}
          >
            Previous
          </Button>

          {currentStep < 6 ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setCurrentStep((prev) => Math.min(6, prev + 1))}
              rightIcon={ArrowRight}
            >
              Continue to Step {currentStep + 1}
            </Button>
          ) : (
            <Button
              variant="accent"
              size="sm"
              isLoading={isSubmitting}
              onClick={handleCreateInvestigation}
              leftIcon={Play}
            >
              Launch Investigation
            </Button>
          )}
        </CardFooter>
      </Card>
    </AppShell>
  )
}
