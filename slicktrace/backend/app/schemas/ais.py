"""SlickTrace v2 — Pydantic schemas for AISQuery"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AISSearchRequest(BaseModel):
    hindcast_run_id: uuid.UUID
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    time_start: datetime
    time_end: datetime
    radius_km: Optional[float] = None
    ais_source: Optional[str] = "local"


class AISQueryResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    hindcast_run_id: uuid.UUID
    time_start: datetime
    time_end: datetime
    radius_km: Optional[float]
    ais_source: Optional[str]
    vessel_count: Optional[int]
    results_summary: Optional[Dict[str, Any]]
    executed_at: datetime

    class Config:
        from_attributes = True

class AISPositionResponse(BaseModel):
    id: uuid.UUID
    mmsi: str
    imo: Optional[str] = None
    vessel_name: Optional[str] = None
    call_sign: Optional[str] = None
    vessel_type: Optional[str] = None
    length: Optional[float] = None
    beam: Optional[float] = None
    draft: Optional[float] = None
    timestamp_utc: datetime
    latitude: float
    longitude: float
    sog: Optional[float] = None
    cog: Optional[float] = None
    heading: Optional[float] = None
    provider: str
    dataset: str

    class Config:
        from_attributes = True
