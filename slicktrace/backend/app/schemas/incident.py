"""SlickTrace v2 — Pydantic schemas for Incident"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.incident import IncidentStatus, IncidentMode


class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    operator: Optional[str] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None


class IncidentResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    operator: str
    status: IncidentStatus
    mode: IncidentMode
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
