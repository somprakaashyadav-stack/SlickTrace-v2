"""
SlickTrace v2 — Imagery Upload Endpoint

Accepts GeoTIFF / COG uploads, validates, hashes SHA-256,
stores in MinIO, records in DB.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import sha256_bytes, EvidenceArtifact
from app.core.storage import get_storage
from app.core.config import settings
from app.models.incident import Incident
from app.models.imagery import Imagery
from app.schemas.imagery import ImageryResponse

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "image/tiff",
    "image/geotiff",
    "application/octet-stream",  # Generic binary (many GeoTIFFs sent as this)
}
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


@router.post("/{incident_id}/imagery", response_model=ImageryResponse, status_code=201)
async def upload_imagery(
    incident_id: uuid.UUID,
    file: UploadFile = File(...),
    sensor: Optional[str] = Form(None, description="e.g. 'Sentinel-1 IW GRD'"),
    polarisation: Optional[str] = Form(None, description="VV | VH | HH | HV"),
    scene_id: Optional[str] = Form(None, description="Copernicus scene ID if known"),
    acquisition_time: Optional[str] = Form(None, description="ISO 8601 UTC acquisition time"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a SAR or optical satellite scene to an incident.

    Accepts GeoTIFF / COG files. Computes SHA-256 hash for evidence manifest.
    Stores file in MinIO.
    """
    # Verify incident exists
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Read file
    raw_bytes = await file.read()
    size_bytes = len(raw_bytes)

    if size_bytes == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds 2 GB limit ({size_bytes} bytes)")

    # Compute SHA-256
    file_hash = sha256_bytes(raw_bytes)

    # Store in MinIO
    storage_key = f"incidents/{incident_id}/imagery/{uuid.uuid4()}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    try:
        storage = get_storage()
        storage.upload_bytes(
            bucket=settings.MINIO_BUCKET_IMAGERY,
            key=storage_key,
            data=raw_bytes,
            content_type=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Storage upload failed: {e}")

    # Parse acquisition time
    acq_time = None
    if acquisition_time:
        try:
            acq_time = datetime.fromisoformat(acquisition_time.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Record in DB
    imagery = Imagery(
        incident_id=incident_id,
        filename=file.filename or "upload.tif",
        storage_key=storage_key,
        sha256=file_hash,
        size_bytes=size_bytes,
        sensor=sensor,
        polarisation=polarisation,
        scene_id=scene_id,
        acquisition_time=acq_time,
        content_type=content_type,
    )
    db.add(imagery)
    await db.flush()
    await db.refresh(imagery)
    return imagery


@router.get("/{incident_id}/imagery", response_model=List[ImageryResponse])
async def list_imagery(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all imagery scenes for an incident."""
    result = await db.execute(
        select(Imagery)
        .where(Imagery.incident_id == incident_id)
        .order_by(Imagery.uploaded_at.desc())
    )
    return result.scalars().all()
