# SlickTrace v2

**Professional Maritime Oil-Spill Investigation & Vessel Attribution Platform**

SlickTrace is a decision-support platform for satellite-based marine oil-spill investigations. It ingests real Sentinel-1 SAR imagery, runs ML-based spill segmentation, performs Lagrangian backward hindcasting using OpenDrift, cross-references historical AIS data, ranks candidate vessels by physical consistency, and produces tamper-evident evidence dossiers.

## Pipeline

```
Satellite Evidence
  → Oil/Look-alike Detection (U-Net++ / DeepLabV3+ / SAM2)
  → Slick Segmentation
  → Ocean-Physics Backward Hindcast (OpenDrift/OpenOil)
  → Historical AIS Search (DuckDB Spatial)
  → Candidate Vessel Analysis
  → Physical Consistency Ranking (XGBoost + Isolation Forest)
  → Counterfactual Verification
  → Explainable Investigation Shortlist
  → Evidence Package (SHA-256 manifest)
  → PDF Dossier (WeasyPrint)
```

## Modes

| Mode | Description |
|---|---|
| `REAL` | All data from live APIs/uploads. No pre-seeded incidents. Missing credentials surface as UNAVAILABLE — never silent fallback. |
| `DEMO` | Offline fixture data for demonstrations. Always shown with a prominent banner. |

## Quick Start (Development)

```bash
# 1. Copy env template
cp infra/.env.example infra/.env
# Edit infra/.env and fill in credentials

# 2. Start infrastructure (DB, Redis, MinIO)
cd infra
docker compose -f docker-compose.dev.yml up -d

# 3. Run DB migrations
cd backend
pip install -r requirements.txt
alembic upgrade head

# 4. Backend
uvicorn app.main:app --reload --port 8000

# 5. ML service
cd ../ml
pip install -r requirements.txt
uvicorn serving.inference_service:app --reload --port 8001

# 6. Frontend
cd ../frontend
npm install
npm run dev
```

## Full Stack (Docker Compose)

```bash
cd infra
cp .env.example .env   # fill in your credentials
docker compose up --build
# Frontend:    http://localhost:3000
# Backend API: http://localhost:8000/docs
# ML Service:  http://localhost:8001/docs
# MinIO:       http://localhost:9001
```

## Project Structure

```
slicktrace/
├── frontend/    # Next.js 14 App Router, TypeScript, Tailwind, Mapbox GL, D3, Chart.js
├── backend/     # FastAPI, Celery, SQLAlchemy, PostGIS, Alembic
├── ml/          # PyTorch U-Net++, DeepLabV3+, SAM2 adapter, XGBoost look-alike
├── ocean/       # OpenDrift/OpenOil, ERA5, CMEMS, HYCOM readers, Monte Carlo
├── ais/         # DuckDB Spatial AIS engine, Isolation Forest anomaly detection
├── evidence/    # SHA-256 manifest, WeasyPrint PDF dossier generation
├── data/        # Raw data directories (gitignored)
├── tests/       # pytest test suites
├── docs/        # MkDocs documentation
└── infra/       # Docker Compose, nginx, DB init scripts
```

## Real Data Sources

| Source | Purpose | Registration |
|---|---|---|
| Copernicus Data Space | Sentinel-1/2 SAR imagery | https://dataspace.copernicus.eu/ |
| Copernicus Marine | Ocean currents (CMEMS) | https://marine.copernicus.eu/ |
| ERA5 / CDS API | Wind fields | https://cds.climate.copernicus.eu/ |
| MarineCadastre | Bulk AIS data (US waters) | https://marinecadastre.gov/ais/ |
| Global Fishing Watch | Optional AIS (global) | https://globalfishingwatch.org/ |
| HYCOM THREDDS | Ocean currents (public fallback) | https://tds.hycom.org/ |

## UNAVAILABLE State Policy

When a required credential or model weight is missing in REAL MODE:
- The API returns HTTP 503 with a clear `unavailable_reason` field
- The UI shows a prominent yellow UNAVAILABLE banner
- **The system never silently falls back to demo data**

## Legacy

The original Streamlit prototype is preserved in `../legacy/` for reference only.

## License

Proprietary — All rights reserved.
