# SlickTrace v2 Documentation

**SlickTrace v2** is a decision-support platform for satellite-based marine oil-spill investigation and vessel attribution.

## Core Pipeline

```
Satellite Evidence (Sentinel-1 SAR / COG)
  → Oil/Look-alike Detection (U-Net++ / DeepLabV3+ / SAM 2)
  → Slick Segmentation Polygon
  → Ocean-Physics Backward Hindcast (OpenDrift/OpenOil Lagrangian particle tracking)
  → Historical AIS Search (DuckDB Spatial / MarineCadastre / GFW)
  → Candidate Vessel Analysis & Trajectory Reconstruction
  → Physical Consistency Ranking (XGBoost + Isolation Forest)
  → Counterfactual Verification (Forward drift validation)
  → Explainable Attribution Shortlist
  → Tamper-Evident Evidence Package (SHA-256 Manifest)
  → Official PDF Dossier (WeasyPrint)
```

## System Contracts

1. **REAL MODE**: Operates strictly on live data feeds or uploaded GeoTIFF scenes. Missing remote sensing or oceanographic APIs surface an explicit `UNAVAILABLE` state.
2. **DEMO MODE**: Isolated sandbox for training and validation with synthetic fixtures. Never silently substituted for real data.
