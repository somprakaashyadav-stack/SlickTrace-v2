"""
SlickTrace v2 — Datasets & Spatial Lake API Endpoint
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter
from app.core.config import settings
from app.core.security import sha256_file

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def list_datasets() -> List[Dict[str, Any]]:
    """
    List all mounted spatial datasets, AIS parquet tables, and environmental NetCDF archives.
    Returns honest filesystem telemetry from the data directories.
    """
    datasets = []
    data_dir = Path("data")
    if not data_dir.exists():
        return datasets

    # Scan data subdirectories
    subdirs = {
        "ais": ("AIS Historical Broadcasts", "Apache Parquet / DuckDB Spatial", "EPSG:4326"),
        "ocean": ("Ocean Hydrodynamics & Wind", "NetCDF4 / CF-1.7", "EPSG:4326"),
        "imagery": ("Satellite Radar SAR Vault", "Cloud Optimized GeoTIFF", "EPSG:4326 / UTM"),
    }

    for subdir_name, (category, fmt, crs) in subdirs.items():
        subpath = data_dir / subdir_name
        if subpath.exists():
            for f in subpath.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    stat = f.stat()
                    size_mb = round(stat.st_size / (1024 * 1024), 2)
                    size_str = f"{size_mb} MB" if size_mb < 1024 else f"{round(size_mb/1024, 2)} GB"
                    
                    datasets.append({
                        "name": f.name,
                        "category": category,
                        "format": fmt,
                        "records": "Indexed File",
                        "size": size_str,
                        "crs": crs,
                        "last_updated": stat.st_mtime,
                        "status": "READY",
                    })

    return datasets
