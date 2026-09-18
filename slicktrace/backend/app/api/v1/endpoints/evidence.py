"""
SlickTrace v2 — Evidence & Dossier API Endpoint

Provides access to the SHA-256 evidence manifest and PDF dossier generation.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.incident import Incident
from app.models.manifest import EvidenceManifestRecord

router = APIRouter()


@router.get("/{incident_id}/manifest")
async def get_manifest(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the tamper-evident SHA-256 evidence manifest for an incident.
    Returns the full manifest JSON including artifact hashes and manifest-level SHA-256.
    """
    result = await db.execute(
        select(EvidenceManifestRecord)
        .where(EvidenceManifestRecord.incident_id == incident_id)
        .order_by(EvidenceManifestRecord.updated_at.desc())
    )
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(
            status_code=404,
            detail=(
                "No evidence manifest found for this incident. "
                "Complete at least one pipeline stage to generate the manifest."
            ),
        )
    return manifest.manifest_body


@router.post("/{incident_id}/dossier", status_code=202)
async def generate_dossier(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger PDF evidence dossier generation for an incident.
    Dispatches a Celery task. Returns task ID.
    Poll for completion, then download at /incidents/{id}/dossier/download.
    """
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    try:
        from app.tasks.dossier_task import generate_dossier_task
        task = generate_dossier_task.delay(str(incident_id))
        return {"status": "queued", "task_id": task.id, "incident_id": str(incident_id)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to dispatch dossier task: {e}")


@router.get("/{incident_id}/dossier/preview")
async def preview_dossier_html(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Render and return the 25-section forensic dossier as an interactive HTML document.
    """
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    from app.models.imagery import Imagery
    from app.models.detection import SpillDetection
    from app.models.hindcast import HindcastRun
    from app.models.candidate import CandidateVessel
    from evidence.dossier.generator import DossierGenerator

    img_res = await db.execute(select(Imagery).where(Imagery.incident_id == incident_id))
    det_res = await db.execute(select(SpillDetection).where(SpillDetection.incident_id == incident_id))
    hind_res = await db.execute(select(HindcastRun).where(HindcastRun.incident_id == incident_id))
    cand_res = await db.execute(
        select(CandidateVessel).where(CandidateVessel.incident_id == incident_id).order_by(CandidateVessel.rank)
    )

    gen = DossierGenerator()
    html_content = gen.render_html(
        incident=incident,
        imagery_list=img_res.scalars().all(),
        detections=det_res.scalars().all(),
        hindcasts=hind_res.scalars().all(),
        candidates=cand_res.scalars().all()[:10],
    )
    return Response(content=html_content, media_type="text/html")


@router.get("/{incident_id}/dossier/download")
async def download_dossier(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Download the generated PDF dossier for an incident.
    Fetches from storage or compiles on demand if not yet cached.
    """
    from app.core.config import settings
    from app.core.storage import get_storage
    from evidence.dossier.generator import DossierGenerator

    storage_key = f"incidents/{incident_id}/dossier/investigation_report.pdf"
    pdf_bytes = None
    try:
        storage = get_storage()
        pdf_bytes = storage.download_bytes(
            bucket=settings.MINIO_BUCKET_DOSSIERS,
            key=storage_key,
        )
    except Exception:
        # Generate on demand
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = result.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

        from app.models.imagery import Imagery
        from app.models.detection import SpillDetection
        from app.models.hindcast import HindcastRun
        from app.models.candidate import CandidateVessel

        img_res = await db.execute(select(Imagery).where(Imagery.incident_id == incident_id))
        det_res = await db.execute(select(SpillDetection).where(SpillDetection.incident_id == incident_id))
        hind_res = await db.execute(select(HindcastRun).where(HindcastRun.incident_id == incident_id))
        cand_res = await db.execute(
            select(CandidateVessel).where(CandidateVessel.incident_id == incident_id).order_by(CandidateVessel.rank)
        )

        gen = DossierGenerator()
        pdf_bytes = gen.generate_pdf(
            incident=incident,
            imagery_list=img_res.scalars().all(),
            detections=det_res.scalars().all(),
            hindcasts=hind_res.scalars().all(),
            candidates=cand_res.scalars().all()[:10],
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="slicktrace_incident_{incident_id}.pdf"'
        },
    )
