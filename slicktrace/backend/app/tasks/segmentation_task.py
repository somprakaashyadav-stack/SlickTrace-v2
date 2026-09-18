"""
SlickTrace v2 — Segmentation Celery Task

Calls the ML inference service, stores results in DB,
updates evidence manifest, broadcasts progress via WebSocket.
"""
from __future__ import annotations

from datetime import datetime, timezone

from celery import Task
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.detection import DetectionStatus


def _get_sync_session() -> Session:
    """Sync SQLAlchemy session for Celery workers (no async)."""
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(
    bind=True,
    name="app.tasks.segmentation_task.run_segmentation",
    max_retries=2,
    default_retry_delay=30,
    queue="ml",
)
def run_segmentation(
    self: Task,
    detection_id: str,
    storage_key: str,
    model: str = "unetplusplus",
    use_sam2: bool = False,
) -> dict:
    """
    Download SAR GeoTIFF from MinIO, send to ML service, store results.
    """
    from app.models.detection import SpillDetection
    from app.core.storage import get_storage

    session = _get_sync_session()

    try:
        # Update status to RUNNING
        detection = session.get(SpillDetection, detection_id)
        if not detection:
            logger.error(f"[SEGMENTATION] Detection {detection_id} not found")
            return

        detection.status = DetectionStatus.RUNNING
        detection.celery_task_id = self.request.id
        session.commit()

        # Download imagery from MinIO
        storage = get_storage()
        raw_bytes = storage.download_bytes(
            bucket=settings.MINIO_BUCKET_IMAGERY,
            key=storage_key,
        )

        # Call ML inference service
        import httpx
        import io

        files = {"file": ("scene.tif", raw_bytes, "image/tiff")}
        data = {"model": model, "use_sam2": str(use_sam2).lower()}

        response = httpx.post(
            f"{settings.ML_SERVICE_URL}/detect",
            files=files,
            data=data,
            timeout=300,  # 5 min timeout for large scenes
        )

        if response.status_code == 503:
            # ML weights unavailable
            result = response.json()
            detection.status = DetectionStatus.UNAVAILABLE
            detection.unavailable_reason = result.get("unavailable_reason", "ML service unavailable")
            detection.completed_at = datetime.now(timezone.utc)
            session.commit()
            logger.warning(f"[SEGMENTATION] UNAVAILABLE: {detection.unavailable_reason}")
            return

        response.raise_for_status()
        result = response.json()

        # Store results
        from geoalchemy2.shape import from_shape
        from shapely.geometry import shape, mapping

        if result.get("spill_geojson") and result["spill_geojson"].get("geometry"):
            geom = shape(result["spill_geojson"]["geometry"])
            detection.spill_polygon = from_shape(geom, srid=4326)
            detection.centroid = from_shape(geom.centroid, srid=4326)

        detection.status = DetectionStatus.DONE
        detection.area_km2 = result.get("area_km2")
        detection.confidence = result.get("confidence")
        detection.lookalike_prob = result.get("lookalike_probability")
        detection.is_oil = result.get("is_oil")
        detection.sam2_refined = result.get("sam2_refined", False)
        detection.model_used = result.get("model_used")
        detection.raw_output = result
        detection.completed_at = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            f"[SEGMENTATION] Done: detection_id={detection_id} "
            f"area={detection.area_km2}km² confidence={detection.confidence:.3f}"
        )
        return {"status": "done", "detection_id": detection_id}

    except Exception as exc:
        logger.exception(f"[SEGMENTATION] Failed: {exc}")
        detection = session.get(SpillDetection, detection_id)
        if detection:
            detection.status = DetectionStatus.FAILED
            detection.error_message = str(exc)
            detection.completed_at = datetime.now(timezone.utc)
            session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()
