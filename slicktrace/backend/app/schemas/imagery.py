"""SlickTrace v2 — Pydantic schemas for Imagery"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ImageryResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    filename: str
    storage_key: str
    sha256: str
    size_bytes: int
    sensor: Optional[str]
    polarisation: Optional[str]
    scene_id: Optional[str]
    acquisition_time: Optional[datetime]
    content_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
