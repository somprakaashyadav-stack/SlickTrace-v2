"""
SlickTrace v2 — Hindcast API Endpoint

Triggers OpenDrift backward Lagrangian simulation via Celery.
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.detection import SpillDetection, DetectionStatus
from app.models.hindcast import HindcastRun, HindcastStatus
from app.schemas.hindcast import HindcastResponse, HindcastTriggerRequest

router = APIRouter()


@router.post("/{incident_id}/hindcast", response_model=HindcastResponse, status_code=202)
async def trigger_hindcast(
    incident_id: uuid.UUID,
    payload: HindcastTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger backward Lagrangian hindcast from a completed spill detection.

    Returns immediately with task ID. Poll for results.
    """
    # Verify detection exists and is completed
    result = await db.execute(
        select(SpillDetection).where(
            SpillDetection.id == payload.detection_id,
            SpillDetection.incident_id == incident_id,
        )
    )
    detection = result.scalar_one_or_none()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    if detection.status != DetectionStatus.DONE:
        raise HTTPException(
            status_code=422,
            detail=f"Detection must be in DONE status (current: {detection.status})",
        )
    if not detection.centroid:
        raise HTTPException(status_code=422, detail="Detection has no centroid geometry")

    sim_cfg = {
        "durations_hours": payload.durations_hours or [4, 8, 12, 24],
        "n_particles": payload.n_particles or 1000,
        "oil_type": payload.oil_type or "GENERIC BUNKER C",
        "allow_fallback": payload.allow_fallback,
        "slick_polygon": payload.slick_polygon,
    }

    # Create hindcast run
    run = HindcastRun(
        incident_id=incident_id,
        detection_id=payload.detection_id,
        status=HindcastStatus.PENDING,
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        detection_time=payload.detection_time,
        hours_back=max(payload.durations_hours or [payload.hours_back or 24]),
        n_particles=payload.n_particles or 1000,
        simulation_config=sim_cfg,
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    # Dispatch Celery task
    try:
        from app.tasks.hindcast_task import run_hindcast_task
        task = run_hindcast_task.delay(str(run.id))
        run.celery_task_id = task.id
        await db.flush()
    except Exception as e:
        run.status = HindcastStatus.FAILED
        run.error_message = str(e)
        await db.flush()
        raise HTTPException(status_code=503, detail=f"Failed to dispatch hindcast task: {e}")

    return run


@router.get("/{incident_id}/hindcast", response_model=List[HindcastResponse])
async def list_hindcasts(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all hindcast runs for an incident."""
    result = await db.execute(
        select(HindcastRun)
        .where(HindcastRun.incident_id == incident_id)
        .order_by(HindcastRun.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{incident_id}/hindcast/{run_id}", response_model=HindcastResponse)
async def get_hindcast(
    incident_id: uuid.UUID,
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single hindcast run result including trajectory GeoJSON."""
    result = await db.execute(
        select(HindcastRun).where(
            HindcastRun.id == run_id,
            HindcastRun.incident_id == incident_id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Hindcast run not found")
    return run
