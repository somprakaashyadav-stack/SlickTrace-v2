"""
SlickTrace v2 — AIS Search API Endpoint

Triggers DuckDB Spatial AIS query against hindcast origin window.
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.hindcast import HindcastRun, HindcastStatus
from app.models.ais_query import AISQuery
from app.schemas.ais import AISQueryResponse, AISSearchRequest

router = APIRouter()


@router.post("/{incident_id}/ais-search", response_model=AISQueryResponse, status_code=202)
async def trigger_ais_search(
    incident_id: uuid.UUID,
    payload: AISSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a spatiotemporal AIS search against the hindcast origin window.

    Uses the DuckDB Spatial engine to query loaded AIS data.
    Returns immediately with query record. Results populated asynchronously.
    """
    # Verify hindcast run
    result = await db.execute(
        select(HindcastRun).where(
            HindcastRun.id == payload.hindcast_run_id,
            HindcastRun.incident_id == incident_id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Hindcast run not found")
    if run.status != HindcastStatus.DONE:
        raise HTTPException(
            status_code=422,
            detail=f"Hindcast must be DONE before AIS search (current: {run.status})",
        )

    # Create AIS query record
    from shapely.geometry import box
    from geoalchemy2.shape import from_shape
    search_box = box(payload.lon_min, payload.lat_min, payload.lon_max, payload.lat_max)

    query_record = AISQuery(
        incident_id=incident_id,
        hindcast_run_id=payload.hindcast_run_id,
        time_start=payload.time_start,
        time_end=payload.time_end,
        search_polygon=from_shape(search_box, srid=4326),
        radius_km=payload.radius_km,
        ais_source=payload.ais_source or "local",
    )
    db.add(query_record)
    await db.flush()
    await db.refresh(query_record)

    # Dispatch Celery task
    try:
        from app.tasks.ais_query_task import run_ais_query
        task = run_ais_query.delay(str(query_record.id))
        await db.flush()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to dispatch AIS query: {e}")

    return query_record


@router.post("/{incident_id}/ais-upload", status_code=200)
async def upload_ais_file(
    incident_id: uuid.UUID,
    file: UploadFile = File(..., description="AIS CSV or Parquet file"),
    source_label: str = Form(default="local_upload"),
):
    """
    Upload a local AIS CSV or Parquet file and ingest it into DuckDB.
    """
    filename = file.filename or "upload"
    raw = await file.read()

    from pathlib import Path
    import tempfile

    suffix = ".parquet" if filename.endswith(".parquet") else ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    try:
        from ais.ingest.marinecadastre import get_duckdb_connection, init_ais_table, load_csv_file, load_parquet_file, AIS_DB_PATH
        conn = get_duckdb_connection(AIS_DB_PATH)
        init_ais_table(conn)

        if suffix == ".parquet":
            count = load_parquet_file(tmp_path, conn, source_label)
        else:
            count = load_csv_file(tmp_path, conn, source_label)

        conn.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"status": "ok", "rows_ingested": count, "source": source_label}


@router.get("/{incident_id}/ais-queries", response_model=List[AISQueryResponse])
async def list_ais_queries(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AISQuery)
        .where(AISQuery.incident_id == incident_id)
        .order_by(AISQuery.executed_at.desc())
    )
    return result.scalars().all()
