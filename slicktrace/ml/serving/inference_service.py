"""
SlickTrace v2 — ML Inference Service (FastAPI microservice)

Endpoints:
  POST /detect  — accept GeoTIFF, run segmentation + look-alike classification
  GET  /health  — service health + per-model weight availability

REAL MODE contract:
  - WeightsUnavailable → HTTP 503 with structured unavailable_reason
  - No mock/synthetic outputs ever returned in real mode
  - SAM2 unavailability is logged + skipped (non-blocking optional step)
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel

from ml.models.weight_guard import WeightsUnavailable
from ml.models.unetplusplus import UNetPlusPlusSegmentor
from ml.models.deeplabv3plus import DeepLabV3PlusSegmentor
from ml.models.sam2_refiner import SAM2Refiner, SAM2RefinerUnavailable
from ml.models.lookalike_classifier import LookalikeClassifier
from ml.serving.preprocessing import (
    load_sar_geotiff,
    mask_to_geojson_polygon,
    PreprocessingError,
)

app = FastAPI(
    title="SlickTrace ML Inference Service",
    description=(
        "SAR oil-spill segmentation (U-Net++, DeepLabV3+, ensemble), "
        "look-alike classification (XGBoost), and optional SAM2 mask refinement."
    ),
    version="2.0.0",
)

# Lazy singletons — loaded on first request
_unet: Optional[UNetPlusPlusSegmentor] = None
_deeplab: Optional[DeepLabV3PlusSegmentor] = None
_sam2: Optional[SAM2Refiner] = None
_lookalike: Optional[LookalikeClassifier] = None

SLICKTRACE_MODE = os.environ.get("SLICKTRACE_MODE", "real").lower()
WEIGHTS_DIR = Path(os.environ.get("ML_WEIGHTS_DIR", "/app/weights"))


class DetectionResponse(BaseModel):
    request_id: str
    status: str           # "done" | "unavailable" | "error"
    model_used: Optional[str] = None
    spill_geojson: Optional[dict] = None
    area_km2: Optional[float] = None
    confidence: Optional[float] = None
    lookalike_probability: Optional[float] = None
    is_oil: Optional[bool] = None
    sam2_refined: bool = False
    unavailable_reason: Optional[str] = None
    processing_time_s: Optional[float] = None


@app.get("/health")
async def health():
    """Return service health + per-model weight availability."""
    return {
        "service": "ok",
        "mode": SLICKTRACE_MODE,
        "models": {
            "unetplusplus_resnet50": {
                "available": (WEIGHTS_DIR / "unetplusplus_resnet50_sar.pth").exists(),
                "path": str(WEIGHTS_DIR / "unetplusplus_resnet50_sar.pth"),
            },
            "deeplabv3plus_resnet50": {
                "available": (WEIGHTS_DIR / "deeplabv3plus_resnet50_sar.pth").exists(),
                "path": str(WEIGHTS_DIR / "deeplabv3plus_resnet50_sar.pth"),
            },
            "lookalike_xgb": {
                "available": (WEIGHTS_DIR / "lookalike_xgb.ubj").exists(),
                "path": str(WEIGHTS_DIR / "lookalike_xgb.ubj"),
            },
            "sam2_hiera_large": {
                "available": (WEIGHTS_DIR / "sam2_hiera_large.pt").exists(),
                "path": str(WEIGHTS_DIR / "sam2_hiera_large.pt"),
                "optional": True,
            },
        },
    }


@app.post("/detect", response_model=DetectionResponse)
async def detect(
    file: UploadFile = File(..., description="SAR GeoTIFF (Sentinel-1 IW GRD or compatible)"),
    model: str = Form(default="unetplusplus", description="unetplusplus | deeplabv3plus | ensemble"),
    use_sam2: bool = Form(default=False, description="Apply optional SAM2 mask refinement"),
    band: int = Form(default=1, description="GeoTIFF band index to read (1-indexed)"),
):
    """
    Run oil-spill segmentation on an uploaded SAR GeoTIFF.

    Returns spill polygon as GeoJSON + look-alike classification probability.
    Returns HTTP 503 (UNAVAILABLE) if required model weights are not present.
    """
    request_id = str(uuid.uuid4())
    t0 = time.time()
    logger.info(f"[DETECT] request_id={request_id} model={model} sam2={use_sam2} band={band}")

    # Write uploaded file to temp
    raw_bytes = await file.read()
    tmp_path = Path(f"/tmp/slicktrace_{request_id}.tif")
    try:
        tmp_path.write_bytes(raw_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write temp file: {e}")

    # Preprocess SAR
    try:
        sar_array, meta = load_sar_geotiff(tmp_path, band=band)
    except PreprocessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    # --- Segmentation ---
    global _unet, _deeplab, _lookalike, _sam2
    mask = None
    model_used = None

    try:
        if model in ("unetplusplus", "ensemble"):
            if _unet is None:
                _unet = UNetPlusPlusSegmentor()
            mask = _unet.predict(sar_array)
            model_used = "unetplusplus_resnet50"

        if model == "deeplabv3plus":
            if _deeplab is None:
                _deeplab = DeepLabV3PlusSegmentor()
            mask = _deeplab.predict(sar_array)
            model_used = "deeplabv3plus_resnet50"

        if model == "ensemble":
            # Average U-Net++ and DeepLabV3+
            if _deeplab is None:
                _deeplab = DeepLabV3PlusSegmentor()
            mask2 = _deeplab.predict(sar_array)
            mask = (mask + mask2) / 2.0
            model_used = "ensemble_unetplusplus_deeplabv3plus"

    except WeightsUnavailable as e:
        logger.warning(f"[DETECT] {e}")
        return DetectionResponse(
            request_id=request_id,
            status="unavailable",
            unavailable_reason=str(e),
        )

    if mask is None:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

    # --- Optional SAM2 refinement ---
    sam2_refined = False
    if use_sam2:
        try:
            if _sam2 is None:
                _sam2 = SAM2Refiner()
            import numpy as np
            rgb = (np.stack([sar_array] * 3, axis=-1) * 255).astype(np.uint8)
            binary_mask = mask >= 0.5
            if binary_mask.any():
                refined = _sam2.refine(rgb, binary_mask)
                mask = refined.astype("float32")
                sam2_refined = True
        except (SAM2RefinerUnavailable, WeightsUnavailable) as e:
            logger.warning(f"[DETECT] SAM2 refinement skipped (unavailable): {e}")

    # --- Build GeoJSON polygon ---
    spill_geojson = mask_to_geojson_polygon(mask, meta["transform"], meta["crs"])
    area_km2 = spill_geojson.get("properties", {}).get("area_km2")
    confidence = float(mask.max())

    # --- Look-alike classification ---
    lookalike_prob: Optional[float] = None
    is_oil: Optional[bool] = None
    try:
        if spill_geojson.get("geometry"):
            if _lookalike is None:
                _lookalike = LookalikeClassifier()
            lookalike_prob = _lookalike.predict_proba(sar_array, mask)
            is_oil = lookalike_prob >= 0.5
    except WeightsUnavailable as e:
        logger.warning(f"[DETECT] Look-alike classifier unavailable: {e}")

    elapsed = round(time.time() - t0, 2)
    logger.info(f"[DETECT] done request_id={request_id} time={elapsed}s")

    return DetectionResponse(
        request_id=request_id,
        status="done",
        model_used=model_used,
        spill_geojson=spill_geojson,
        area_km2=area_km2,
        confidence=confidence,
        lookalike_probability=lookalike_prob,
        is_oil=is_oil,
        sam2_refined=sam2_refined,
        processing_time_s=elapsed,
    )
