"""
SlickTrace v2 — Environmental Forcing Pydantic Schemas
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ForcingQueryRequest(BaseModel):
    lon_min: float = Field(..., ge=-180.0, le=180.0)
    lat_min: float = Field(..., ge=-90.0, le=90.0)
    lon_max: float = Field(..., ge=-180.0, le=180.0)
    lat_max: float = Field(..., ge=-90.0, le=90.0)
    time_start: str = Field(..., description="ISO-8601 timestamp")
    time_end: str = Field(..., description="ISO-8601 timestamp")
    allow_fallback: bool = Field(default=False, description="Allow public HYCOM fallback if CMEMS is unavailable")
    use_cache: bool = Field(default=True, description="Check local forcing cache before remote download")


class ForcingProvenanceSchema(BaseModel):
    source_name: str
    dataset_id: str
    dataset_version: str
    source_url: str
    raw_file_sha256: str
    spatial_bounds: Dict[str, float]
    time_range: Dict[str, str]
    retrieved_at: str
    execution_duration_sec: float
    notes: List[str] = []


class NormalizedForcingResponse(BaseModel):
    variable_type: str
    source: str
    dataset_version: str
    resolution: str
    timestamp: List[str]
    latitude: List[float]
    longitude: List[float]
    shape: List[int]
    speed_min_ms: float
    speed_max_ms: float
    speed_mean_ms: float
    provenance: Optional[ForcingProvenanceSchema] = None


class ProviderStatusResponse(BaseModel):
    era5_wind: Dict[str, Any]
    cmems_currents: Dict[str, Any]
    hycom_currents: Dict[str, Any]
    incois_currents: Dict[str, Any]
    cmems_waves: Dict[str, Any]
