"""
SlickTrace v2 — Copernicus Data Space API Endpoints

Provides catalog searching, metadata extraction, authenticated downloads,
and direct ingestion into incidents as SatelliteEvidence.
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.copernicus import (
    CopernicusDownloadRequest,
    CopernicusProductItem,
    CopernicusSearchRequest,
    CopernicusSearchResponse,
)
from app.services.copernicus_adapter import (
    CopernicusDataSpaceAdapter,
    CopernicusProviderUnavailable,
)

router = APIRouter()


@router.get("/status")
async def get_copernicus_status():
    """Check Copernicus Data Space Ecosystem (CDSE) API availability."""
    adapter = CopernicusDataSpaceAdapter()
    available, reason = adapter.check_availability()
    return {
        "provider": "Copernicus Data Space Ecosystem (CDSE)",
        "available": available,
        "reason": reason,
        "registration_url": "https://dataspace.copernicus.eu/",
        "supported_missions": ["Sentinel-1 (SAR GRD/SLC)", "Sentinel-2 (Optical L1C/L2A)"],
    }


@router.post("/search", response_model=CopernicusSearchResponse)
async def search_copernicus_catalog(payload: CopernicusSearchRequest):
    """
    Search live Copernicus Data Space catalog for real Sentinel-1 and Sentinel-2 scenes.

    If credentials are missing or API is unreachable, clearly exposes the
    provider-unavailable state with registration URL.
    Never fabricates fake products.
    """
    adapter = CopernicusDataSpaceAdapter()
    available, reason = adapter.check_availability()
    if not available:
        return CopernicusSearchResponse(
            provider_status="unavailable",
            unavailable_reason=reason,
            total_results=0,
            products=[],
        )

    try:
        raw_products = adapter.search_products(
            platform=payload.platform,
            date_from=payload.date_from,
            date_to=payload.date_to,
            aoi_wkt=payload.aoi_wkt,
            product_type=payload.product_type,
            polarization=payload.polarization,
            max_cloud_cover=payload.max_cloud_cover,
            limit=payload.limit,
        )

        items = [
            CopernicusProductItem(
                id=p["id"],
                name=p["name"],
                content_length_bytes=p["content_length_bytes"],
                content_date_start=p["content_date_start"],
                content_date_end=p["content_date_end"],
                platform=p["platform"],
                sensor=p["sensor"],
                product_type=p["product_type"],
                polarization=p["polarization"],
                cloud_cover_percent=p["cloud_cover_percent"],
                footprint_geojson=p["footprint_geojson"],
                quicklook_url=p["quicklook_url"],
            )
            for p in raw_products
        ]

        return CopernicusSearchResponse(
            provider_status="available",
            unavailable_reason=None,
            total_results=len(items),
            products=items,
        )

    except CopernicusProviderUnavailable as e:
        return CopernicusSearchResponse(
            provider_status="unavailable",
            unavailable_reason=str(e.message),
            total_results=0,
            products=[],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@router.get("/products/{product_id}")
async def get_copernicus_product_details(product_id: str):
    """Fetch complete metadata attributes for a specific product ID."""
    adapter = CopernicusDataSpaceAdapter()
    try:
        meta = adapter.get_product_metadata(product_id)
        return meta
    except CopernicusProviderUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/download")
async def download_and_cache_copernicus_product(
    payload: CopernicusDownloadRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Download a selected Sentinel scene from CDSE, cache in MinIO, validate,
    and optionally link directly to an incident as SatelliteEvidence.
    """
    adapter = CopernicusDataSpaceAdapter()
    available, reason = adapter.check_availability()
    if not available:
        raise HTTPException(status_code=503, detail=f"Copernicus API unavailable: {reason}")

    # 1. Fetch metadata first to get product filename
    meta = adapter.get_product_metadata(payload.product_id)
    product_name = meta.get("name") or f"{payload.product_id}.zip"

    # 2. Download to temp file
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = Path(tmp_dir) / product_name
        try:
            adapter.download_product(payload.product_id, target_path)
        except CopernicusProviderUnavailable as e:
            raise HTTPException(status_code=503, detail=str(e))

        # 3. Cache product in MinIO
        storage_key, sha256_hash, size_bytes = adapter.cache_product(payload.product_id, target_path)

        # 4. Validate product
        validation_report = adapter.validate_product(target_path)

        # 5. If incident_id provided, ingest directly as SatelliteEvidence
        evidence_id = None
        if payload.incident_id:
            from app.models.satellite_evidence import SatelliteEvidence, EvidenceProcessingStatus
            evidence_record = SatelliteEvidence(
                incident_id=payload.incident_id,
                filename=product_name,
                storage_key=storage_key,
                file_hash=sha256_hash,
                size_bytes=size_bytes,
                platform=meta.get("platform"),
                sensor=meta.get("sensor"),
                product_type=meta.get("product_type"),
                polarization=meta.get("polarization"),
                acquisition_time=datetime.fromisoformat(meta["content_date_start"].replace("Z", "+00:00")) if meta.get("content_date_start") else None,
                temporal_attribution_available=bool(meta.get("content_date_start")),
                is_georeferenced=bool(meta.get("footprint_geojson")),
                geospatial_attribution_available=bool(meta.get("footprint_geojson")),
                processing_status=EvidenceProcessingStatus.READY,
                validation_notes=[f"Ingested from Copernicus Data Space (ID: {payload.product_id})"],
                raw_metadata=meta.get("raw_attributes"),
            )
            db.add(evidence_record)
            await db.flush()
            await db.refresh(evidence_record)
            evidence_id = str(evidence_record.id)

        return {
            "status": "downloaded_and_cached",
            "product_id": payload.product_id,
            "filename": product_name,
            "storage_key": storage_key,
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
            "validation": validation_report,
            "ingested_evidence_id": evidence_id,
        }
