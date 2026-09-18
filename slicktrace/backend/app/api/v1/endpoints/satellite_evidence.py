"""
SlickTrace v2 — Satellite Evidence API Endpoints

Handles satellite evidence scene uploads (Sentinel-1 SAR GRD, Sentinel-2 optical,
COG, GeoTIFF), metadata extraction, georeferencing/temporal attribution validation,
and analysis-ready raster generation.
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from geoalchemy2.shape import from_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.storage import get_storage
from app.models.incident import Incident
from app.models.satellite_evidence import EvidenceProcessingStatus, SatelliteEvidence
from app.schemas.satellite_evidence import SatelliteEvidenceResponse, SatelliteEvidenceSummary
from app.services.satellite_ingest import SatelliteIngestError, SatelliteIngestService

router = APIRouter()

MAX_SATELLITE_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB limit


@router.post(
    "/{incident_id}/satellite-evidence",
    response_model=SatelliteEvidenceResponse,
    status_code=201,
)
async def upload_satellite_evidence(
    incident_id: uuid.UUID,
    file: UploadFile = File(..., description="Sentinel-1 / Sentinel-2 / COG GeoTIFF file"),
    platform_override: Optional[str] = Form(None, description="Optional override: Sentinel-1A | Sentinel-2B"),
    polarization_override: Optional[str] = Form(None, description="Optional override: VV | VH | VV+VH"),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a satellite scene as forensic evidence:
    1. Stream file to disk & calculate SHA-256.
    2. Extract satellite platform, sensor, CRS, and georeferencing.
    3. Validate acquisition timestamp (flagging attribution availability without inventing).
    4. Save original file to MinIO object storage.
    5. Generate analysis-ready raster product if SAR.
    6. Persist database record with full forensic metadata.
    """
    # 1. Verify incident exists
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    filename = file.filename or "satellite_scene.tif"
    suffix = Path(filename).suffix or ".tif"

    # Save to temp file for Rasterio inspection
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        while True:
            chunk = await file.read(65536)
            if not chunk:
                break
            tmp.write(chunk)

    try:
        size_bytes = tmp_path.stat().st_size
        if size_bytes == 0:
            raise HTTPException(status_code=422, detail="Uploaded satellite raster is empty (0 bytes).")
        if size_bytes > MAX_SATELLITE_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"Raster exceeds 2 GB limit ({size_bytes} bytes).")

        # 2. Run Inspection & Metadata Extraction Subsystem
        try:
            inspection = SatelliteIngestService.inspect_and_validate(tmp_path, filename)
        except SatelliteIngestError as e:
            raise HTTPException(status_code=422, detail=f"Satellite raster validation rejected: {e}")

        # Apply user overrides if provided
        if platform_override:
            inspection["platform"] = platform_override
        if polarization_override:
            inspection["polarization"] = polarization_override

        # 3. Store Original to MinIO
        storage = get_storage()
        raw_storage_key = f"incidents/{incident_id}/satellite/{inspection['file_hash'][:16]}_{filename}"
        storage.upload_file(
            bucket=settings.MINIO_BUCKET_IMAGERY,
            key=raw_storage_key,
            file_path=tmp_path,
        )

        # 4. Generate Analysis-Ready Raster if SAR
        analysis_ready_key = None
        status = EvidenceProcessingStatus.READY

        is_sar = (
            (inspection["platform"] and "Sentinel-1" in inspection["platform"])
            or (inspection["sensor"] and "SAR" in inspection["sensor"])
            or "GRD" in (inspection["product_type"] or "")
        )

        if is_sar and inspection["is_georeferenced"]:
            analysis_tmp = tmp_path.with_name(f"analysis_ready_{tmp_path.name}")
            try:
                SatelliteIngestService.preprocess_sar_to_analysis_ready(tmp_path, analysis_tmp)
                analysis_ready_key = f"incidents/{incident_id}/satellite/ar_{inspection['file_hash'][:16]}.tif"
                storage.upload_file(
                    bucket=settings.MINIO_BUCKET_OUTPUTS,
                    key=analysis_ready_key,
                    file_path=analysis_tmp,
                )
            except Exception as ex:
                status = EvidenceProcessingStatus.READY  # Still keep ready with raw, record note
                inspection["validation_notes"].append(f"Analysis-ready preprocessing note: {ex}")
            finally:
                analysis_tmp.unlink(missing_ok=True)

        # 5. Build Database Record
        bbox_geom = None
        if inspection["bbox_polygon"] is not None:
            bbox_geom = from_shape(inspection["bbox_polygon"], srid=4326)

        evidence_record = SatelliteEvidence(
            incident_id=incident_id,
            filename=filename,
            storage_key=raw_storage_key,
            file_hash=inspection["file_hash"],
            size_bytes=inspection["size_bytes"],
            content_type="image/tiff",
            platform=inspection["platform"],
            sensor=inspection["sensor"],
            product_type=inspection["product_type"],
            polarization=inspection["polarization"],
            acquisition_time=inspection["acquisition_time"],
            temporal_attribution_available=inspection["temporal_attribution_available"],
            crs=inspection["crs"],
            crs_epsg=inspection["crs_epsg"],
            is_georeferenced=inspection["is_georeferenced"],
            geospatial_attribution_available=inspection["geospatial_attribution_available"],
            bbox=bbox_geom,
            resolution_x_m=inspection["resolution_x_m"],
            resolution_y_m=inspection["resolution_y_m"],
            width=inspection["width"],
            height=inspection["height"],
            bands=inspection["bands"],
            nodata_value=inspection["nodata_value"],
            dtype=inspection["dtype"],
            analysis_ready_storage_key=analysis_ready_key,
            processing_status=status,
            validation_notes=inspection["validation_notes"],
            raw_metadata=inspection["raw_metadata"],
        )

        db.add(evidence_record)
        await db.flush()
        await db.refresh(evidence_record)
        return evidence_record

    finally:
        tmp_path.unlink(missing_ok=True)


@router.get(
    "/{incident_id}/satellite-evidence",
    response_model=List[SatelliteEvidenceSummary],
)
async def list_satellite_evidence(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all ingested satellite evidence scenes for an incident."""
    result = await db.execute(
        select(SatelliteEvidence)
        .where(SatelliteEvidence.incident_id == incident_id)
        .order_by(SatelliteEvidence.created_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/{incident_id}/satellite-evidence/{evidence_id}",
    response_model=SatelliteEvidenceResponse,
)
async def get_satellite_evidence_details(
    incident_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full forensic metadata and validation status for a satellite scene."""
    result = await db.execute(
        select(SatelliteEvidence).where(
            SatelliteEvidence.id == evidence_id,
            SatelliteEvidence.incident_id == incident_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Satellite evidence record not found.")
    return record


@router.get("/{incident_id}/satellite-evidence/{evidence_id}/download")
async def download_satellite_evidence(
    incident_id: uuid.UUID,
    evidence_id: uuid.UUID,
    variant: str = "original",  # "original" or "analysis_ready"
    db: AsyncSession = Depends(get_db),
):
    """Download original or analysis-ready satellite raster file."""
    result = await db.execute(
        select(SatelliteEvidence).where(
            SatelliteEvidence.id == evidence_id,
            SatelliteEvidence.incident_id == incident_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Satellite evidence record not found.")

    storage = get_storage()
    if variant == "analysis_ready" and record.analysis_ready_storage_key:
        bucket = settings.MINIO_BUCKET_OUTPUTS
        key = record.analysis_ready_storage_key
        filename = f"analysis_ready_{record.filename}"
    else:
        bucket = settings.MINIO_BUCKET_IMAGERY
        key = record.storage_key
        filename = record.filename

    try:
        data = storage.download_bytes(bucket, key)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Storage retrieval failed: {e}")

    return Response(
        content=data,
        media_type="image/tiff",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
