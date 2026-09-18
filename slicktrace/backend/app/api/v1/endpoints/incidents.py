"""
SlickTrace v2 — Incidents API Endpoint
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.incident import Incident, IncidentMode, IncidentStatus
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate

router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new investigation incident.

    In REAL MODE, mode is always set to 'real'.
    In DEMO MODE, mode is 'demo' and a warning is included.
    """
    mode = IncidentMode.DEMO if settings.is_demo_mode else IncidentMode.REAL

    incident = Incident(
        title=payload.title,
        description=payload.description,
        operator=payload.operator or "system",
        status=IncidentStatus.OPEN,
        mode=mode,
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)
    return incident


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all investigation incidents."""
    q = select(Incident).order_by(Incident.created_at.desc()).offset(offset).limit(limit)
    if status:
        q = q.where(Incident.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single incident by ID."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update incident title, description, or status."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    if payload.title is not None:
        incident.title = payload.title
    if payload.description is not None:
        incident.description = payload.description
    if payload.status is not None:
        incident.status = payload.status

    await db.flush()
    await db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an incident and all associated data."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    await db.delete(incident)
