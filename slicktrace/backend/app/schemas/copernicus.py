"""
SlickTrace v2 — Pydantic Schemas for Copernicus Data Space Adapter
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopernicusSearchRequest(BaseModel):
    platform: str = Field(default="SENTINEL-1", description="SENTINEL-1 or SENTINEL-2")
    date_from: datetime = Field(description="Start of temporal search window")
    date_to: datetime = Field(description="End of temporal search window")
    aoi_wkt: Optional[str] = Field(default=None, description="AOI Polygon in WKT (e.g., POLYGON((-91 27, -89 27, -89 29, -91 29, -91 27)))")
    product_type: Optional[str] = Field(default=None, description="GRD | SLC | L1C | L2A")
    polarization: Optional[str] = Field(default=None, description="VV | VH | VV+VH | HH")
    max_cloud_cover: Optional[float] = Field(default=None, description="Max cloud cover % for optical (0-100)")
    limit: int = Field(default=20, ge=1, le=50)


class CopernicusProductItem(BaseModel):
    id: str
    name: str
    content_length_bytes: int
    content_date_start: Optional[str] = None
    content_date_end: Optional[str] = None
    platform: Optional[str] = None
    sensor: Optional[str] = None
    product_type: Optional[str] = None
    polarization: Optional[str] = None
    cloud_cover_percent: Optional[float] = None
    footprint_geojson: Optional[Dict[str, Any]] = None
    quicklook_url: Optional[str] = None


class CopernicusSearchResponse(BaseModel):
    provider_status: str  # "available" or "unavailable"
    unavailable_reason: Optional[str] = None
    registration_url: str = "https://dataspace.copernicus.eu/"
    total_results: int
    products: List[CopernicusProductItem]


class CopernicusDownloadRequest(BaseModel):
    product_id: str
    incident_id: Optional[uuid.UUID] = Field(
        default=None,
        description="If provided, downloaded product is ingested directly as SatelliteEvidence",
    )
