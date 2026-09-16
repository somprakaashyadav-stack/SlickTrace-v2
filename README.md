# SlickTrace v2 - Maritime Oil Spill Detection & Origin Reconstruction Platform

**SlickTrace v2** is a software architecture built for the Smart India Hackathon. It integrates satellite imagery (Sentinel-1/2 SAR), ocean physics drift modelling (Lagrangian particle simulation), AIS vessel trajectory correlation, multi-factor anomaly scoring, and physics verification to pinpoint and verify oil spill origins and identify suspect vessels.

---

## Architecture Overview

```
SlickTrace-v2/
├── frontend/             # React 18 + Vite + TypeScript + Tailwind CSS Dashboard
├── backend/              # Python FastAPI server + Pydantic + Geo-processing engine
│   ├── services/
│   │   ├── satellite/    # Satellite Data Ingestion & Preprocessing Service:
│   │   │   ├── ingestion.py     # Sentinel-1 SAR & Sentinel-2 Granule loader
│   │   │   ├── preprocessing.py # Lee 5x5 Speckle Filter, Land Masking & Normalization
│   │   │   ├── schemas.py       # Pydantic response models
│   │   │   └── routes.py        # /api/satellite/process & /api/satellite/status
│   │   └── detection/    # AI Oil Spill Detection & Look-Alike Rejection Module:
│   │       ├── model.py         # PyTorch U-Net & DeepLabV3+ model architectures
│   │       ├── lookalike.py     # Look-Alike Rejection Engine (wind, wakes, algae)
│   │       ├── inference.py     # Segmentation manager (DEMO MODE vs MODEL MODE)
│   │       ├── schemas.py       # Pydantic detection schemas
│   │       └── routes.py        # /api/detection/run & /api/detection/result/{spill_id}
│   ├── ingestion/        # Satellite & AIS data ingestors
│   ├── preprocessing/    # SAR noise reduction & land masking
│   ├── detection/        # Dark spot oil slick segmentation
│   ├── characterization/ # Area, thickness & confidence estimation
│   ├── drift/            # Ocean current & wind backward drift simulator
│   ├── origin/           # Probable origin spatio-temporal ellipse builder
│   ├── ais/              # Vessel track query & corridor analysis
│   ├── anomaly/          # Vessel behavior anomaly evaluator
│   ├── scoring/          # Multi-criteria suspect ranking engine
│   ├── physics_verification/ # Forward re-simulation hydrodynamics
│   └── reporting/        # Evidence dossier report exporter
├── data/
│   ├── sample/           # Synthetic datasets generated deterministically (seed=42)
│   │   ├── generate_demo_data.py  # Deterministic data generator script
│   │   ├── generate_sample_sar.py # Synthetic 64x64 SAR backscatter array generator
│   │   ├── sample_sar_scene.json  # Sample Sentinel-1 IW SAR backscatter array
│   │   ├── spill.json      # Satellite oil spill observation (polygon, area, confidence)
│   │   ├── vessels.json    # Metadata for 8 diverse vessels
│   │   ├── ais_tracks.json # AIS trajectories (gaps, course deviations, speed drops)
│   │   └── metocean.json   # Wind & ocean current vector fields
│   ├── satellite/        # Satellite SAR image cache
│   ├── ais/              # Vessel AIS track cache
│   └── metocean/         # Wind & ocean current netCDF/GRIB cache
├── models/               # Model weights & AI classifier checkpoints (.pth files)
├── simulations/          # Physics drift particle cache
├── reports/              # Generated PDF/JSON evidence dossiers
├── docs/                 # Documentation & API specs
├── docker/               # Dockerfiles for container deployment
├── .env.example          # Environment variables template
├── README.md             # Setup and run guide
└── docker-compose.yml    # Full stack Docker orchestrator
```

---

## AI Oil Spill Detection & Look-Alike Rejection Module

The **Detection Service Package** (`backend/services/detection/`) segments preprocessed SAR imagery and filters out marine false positives following an end-to-end pipeline:

```
Preprocessed SAR Array
        ↓
1. AI Segmentation (model.py - Interchangeable PyTorch U-Net or DeepLabV3+)
        ↓
2. Candidate Slick Mask (inference.py)
        ↓
3. Look-Alike Rejection Engine (lookalike.py)
   ├── Low-Wind Calm Zone Filter (Wind < 3.0 m/s causes specular dark reflection)
   ├── Ship Wake Geometry Filter (Vessel trail spatial overlap check)
   ├── Algae / Biological Bloom Filter (SST & texture homogeneity)
   └── Compactness & Aspect Ratio Filter (Perimeter-to-area circularity check)
        ↓
4. Final Verified Slick Polygon & Metrics
```

### PyTorch Architectures & Honest Mode Labeling
- **Interchangeable Models**: Supports **U-Net** (4-level encoder-decoder) and **DeepLabV3+** (ASPP multi-scale pooling) in `backend/services/detection/model.py`.
- **Honest Mode Labeling**:
  - If trained `.pth` weights exist in `models/`, the engine runs in `MODEL MODE (PyTorch Weights Inferred)`.
  - If no weights exist in `models/`, the engine runs in `DEMO / SYNTHETIC (No trained weights in models/)` mode, avoiding false claims about untrained model outputs.

### Detection API Endpoints
- `POST /api/detection/run`: Triggers AI segmentation pipeline (`model_architecture`: `"U-Net"` or `"DeepLabV3+"`) and returns slick geometry, look-alike rejection scorecard, and confidence.
- `GET /api/detection/result/{spill_id}`: Retrieves stored segmentation result and look-alike checks for a given spill ID.

---

## Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

---

### Backend Setup (FastAPI)

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Run the FastAPI development server:
   ```bash
   python backend/main.py
   # Or using uvicorn:
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Check backend status:
   - OpenAPI Docs: `http://localhost:8000/docs`
   - Health Endpoint: `http://localhost:8000/api/health`

---

### Frontend Setup (React + Vite + TypeScript)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Run Vite development server:
   ```bash
   npm run dev
   ```
3. Access Dashboard UI in browser:
   - Dashboard: `http://localhost:5173`
