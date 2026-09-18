"""
SlickTrace v2 — PDF Dossier Generation Celery Task

Generates a tamper-evident PDF dossier using WeasyPrint.
Sections: Incident Summary, Satellite Evidence, Spill Geometry,
Hindcast Results, AIS Candidates, Physical Ranking,
Counterfactual Verification, Evidence Manifest.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from celery import Task
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.celery_app import celery_app
from app.core.config import settings


def _get_sync_session() -> Session:
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(
    bind=True,
    name="app.tasks.dossier_task.generate_dossier_task",
    max_retries=1,
    queue="reporting",
)
def generate_dossier_task(self: Task, incident_id: str) -> dict:
    """Generate PDF evidence dossier for an incident."""
    from app.models.incident import Incident
    from app.models.imagery import Imagery
    from app.models.detection import SpillDetection
    from app.models.hindcast import HindcastRun
    from app.models.candidate import CandidateVessel
    from app.models.manifest import EvidenceManifestRecord
    from app.core.security import EvidenceManifest as SecManifest, EvidenceArtifact, sha256_bytes
    from app.core.storage import get_storage

    session = _get_sync_session()

    try:
        incident = session.get(Incident, incident_id)
        if not incident:
            logger.error(f"[DOSSIER] Incident {incident_id} not found")
            return

        imagery_list = session.query(Imagery).filter(Imagery.incident_id == incident_id).all()
        detections = session.query(SpillDetection).filter(SpillDetection.incident_id == incident_id).all()
        hindcasts = session.query(HindcastRun).filter(HindcastRun.incident_id == incident_id).all()
        candidates = (
            session.query(CandidateVessel)
            .filter(CandidateVessel.incident_id == incident_id)
            .order_by(CandidateVessel.rank)
            .all()
        )

        # Build evidence manifest
        manifest = SecManifest(incident_id=str(incident_id))

        for img in imagery_list:
            manifest.register(EvidenceArtifact(
                artifact_type="satellite_imagery",
                sha256=img.sha256,
                size_bytes=img.size_bytes,
                storage_key=img.storage_key,
                description=f"SAR scene: {img.filename}",
                metadata={"sensor": img.sensor, "scene_id": img.scene_id},
            ))

        manifest_data = manifest.export()

        # Render 25-section forensic PDF dossier via DossierGenerator (ReportLab + embedded charts)
        from evidence.dossier.generator import DossierGenerator
        generator = DossierGenerator()
        pdf_bytes = generator.generate_pdf(
            incident=incident,
            imagery_list=imagery_list,
            detections=detections,
            hindcasts=hindcasts,
            candidates=candidates[:10],
            manifest=manifest_data,
        )

        # Store PDF in MinIO
        storage_key = f"incidents/{incident_id}/dossier/investigation_report.pdf"
        storage = get_storage()
        storage.upload_bytes(
            bucket=settings.MINIO_BUCKET_DOSSIERS,
            key=storage_key,
            data=pdf_bytes,
            content_type="application/pdf",
        )

        # Persist manifest in DB
        manifest_json = json.dumps(manifest_data)
        manifest_hash = sha256_bytes(manifest_json.encode())

        existing = session.query(EvidenceManifestRecord).filter(
            EvidenceManifestRecord.incident_id == incident_id
        ).first()

        if existing:
            existing.manifest_sha256 = manifest_hash
            existing.manifest_body = manifest_data
            existing.storage_key = storage_key
        else:
            rec = EvidenceManifestRecord(
                incident_id=incident_id,
                manifest_sha256=manifest_hash,
                manifest_body=manifest_data,
                storage_key=storage_key,
            )
            session.add(rec)

        session.commit()

        logger.info(f"[DOSSIER] Generated: incident={incident_id} size={len(pdf_bytes)} bytes")
        return {"status": "done", "incident_id": incident_id, "pdf_size_bytes": len(pdf_bytes)}

    except Exception as exc:
        logger.exception(f"[DOSSIER] Failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()
