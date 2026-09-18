# System Architecture

SlickTrace v2 is organized as a high-performance monorepo:

- **Frontend**: Next.js 14 App Router, React, TypeScript, Tailwind CSS, Mapbox GL JS, CesiumJS, Chart.js, D3.js, Socket.io.
- **Backend**: FastAPI, SQLAlchemy Async, PostgreSQL + PostGIS, DuckDB Spatial, Redis, Celery workers, MinIO S3 object storage.
- **ML Microservice**: PyTorch, U-Net++, DeepLabV3+, SAM 2 mask refinement, XGBoost look-alike classifier, Isolation Forest anomaly detector.
- **Ocean Physics Engine**: OpenDrift OpenOil Lagrangian particle tracking with ERA5 atmospheric wind and CMEMS/HYCOM surface hydrodynamic currents.
- **AIS Query Engine**: DuckDB Spatial spatiotemporal envelope querying with MarineCadastre and Global Fishing Watch adapters.
- **Evidence & Dossier**: SHA-256 cryptographic chain-of-custody manifest and WeasyPrint PDF report generation.
