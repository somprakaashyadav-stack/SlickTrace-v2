"""SlickTrace v2 — Pydantic schemas for HindcastRun"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel
from app.models.hindcast import HindcastStatus


class HindcastTriggerRequest(BaseModel):
    detection_id: uuid.UUID
    start_lat: float
    start_lon: float
    detection_time: datetime
    hours_back: Optional[int] = 24
    durations_hours: Optional[List[int]] = [4, 8, 12, 24]
    n_particles: Optional[int] = 1000
    oil_type: Optional[str] = "GENERIC BUNKER C"
    allow_fallback: bool = False
    slick_polygon: Optional[Dict[str, Any]] = None


class HindcastResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    detection_id: uuid.UUID
    status: HindcastStatus
    start_lat: float
    start_lon: float
    detection_time: datetime
    hours_back: int
    n_particles: int
    wind_reader: Optional[str] = None
    current_reader: Optional[str] = None
    origin_time_start: Optional[datetime] = None
    origin_time_end: Optional[datetime] = None
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    trajectory_geojson: Optional[Dict[str, Any]] = None
    particle_timesteps_geojson: Optional[Dict[str, Any]] = None
    uncertainty_metadata: Optional[Dict[str, Any]] = None
    duration_slices: Optional[Dict[str, Any]] = None
    simulation_config: Optional[Dict[str, Any]] = None
    forcing_provenance: Optional[Dict[str, Any]] = None
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

