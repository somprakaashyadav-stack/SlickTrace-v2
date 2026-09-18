"""
SlickTrace v2 — Detection API Endpoint

Triggers ML segmentation job via Celery, polls task status,
returns spill detection results.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.detection import SpillDetection, DetectionStatus
from app.models.imagery import Imagery
from app.schemas.detection import DetectionResponse, DetectionTriggerRequest

router = APIRouter()


@router.post("/{incident_id}/detect", response_model=DetectionResponse, status_code=202)
async def trigger_detection(
    incident_id: uuid.UUID,
    payload: DetectionTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger ML oil-spill segmentation on an uploaded SAR scene.

    Dispatches a Celery task and returns immediately with task ID.
    Poll GET /incidents/{id}/detections/{detection_id} for results.
    """
    # Verify imagery exists
    result = await db.execute(
        select(Imagery).where(
            Imagery.id == payload.imagery_id,
            Imagery.incident_id == incident_id,
        )
    )
    imagery = result.scalar_one_or_none()
    if not imagery:
        raise HTTPException(
            status_code=404,
            detail=f"Imagery {payload.imagery_id} not found in incident {incident_id}",
        )

    # Create detection record
    detection = SpillDetection(
        incident_id=incident_id,
        imagery_id=payload.imagery_id,
        status=DetectionStatus.PENDING,
    )
    db.add(detection)
    await db.flush()
    await db.refresh(detection)

    # Dispatch Celery task
    try:
        from app.tasks.segmentation_task import run_segmentation
        task = run_segmentation.delay(
            str(detection.id),
            str(imagery.storage_key),
            payload.model or "unetplusplus",
            payload.use_sam2 or False,
        )
        detection.celery_task_id = task.id
        await db.flush()
    except Exception as e:
        detection.status = DetectionStatus.FAILED
        detection.error_message = str(e)
        await db.flush()
        raise HTTPException(status_code=503, detail=f"Failed to dispatch segmentation task: {e}")

    return detection


@router.get("/{incident_id}/detections", response_model=List[DetectionResponse])
async def list_detections(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all detection results for an incident."""
    result = await db.execute(
        select(SpillDetection)
        .where(SpillDetection.incident_id == incident_id)
        .order_by(SpillDetection.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{incident_id}/detections/{detection_id}", response_model=DetectionResponse)
async def get_detection(
    incident_id: uuid.UUID,
    detection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single detection result."""
    result = await db.execute(
        select(SpillDetection).where(
            SpillDetection.id == detection_id,
            SpillDetection.incident_id == incident_id,
        )
    )
    detection = result.scalar_one_or_none()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection
