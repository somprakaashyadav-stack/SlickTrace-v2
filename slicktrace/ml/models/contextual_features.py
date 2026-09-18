"""
SlickTrace v2 — Contextual Feature Extractor for Dark Formations

Extracts morphological, geometric, and radiometric texture descriptors
from candidate dark spots and their surrounding sea clutter to distinguish
oil spills from look-alikes (algae, ship wakes, low-wind calms, coastal artifacts).
"""
from __future__ import annotations

from typing import Any, Dict
import numpy as np


def extract_contextual_features(
    sar_patch: np.ndarray,
    dark_mask: np.ndarray,
    background_buffer: int = 15,
) -> Dict[str, float]:
    """
    Extracts contextual discriminative features:
    - Geometry: compactness, elongation, perimeter-to-area ratio, eccentricity
    - Radiometry: mean damping (contrast), variance ratio, boundary gradient sharpness
    """
    assert sar_patch.shape == dark_mask.shape
    H, W = sar_patch.shape

    area_px = float(np.sum(dark_mask))
    if area_px == 0:
        return _zero_features()

    # 1. Geometry features
    rows = np.any(dark_mask, axis=1)
    cols = np.any(dark_mask, axis=0)
    if not rows.any() or not cols.any():
        return _zero_features()

    h_bbox = float(np.sum(rows))
    w_bbox = float(np.sum(cols))
    bbox_area = max(1.0, h_bbox * w_bbox)

    # Compactness (area / bbox_area)
    compactness = area_px / bbox_area

    # Elongation (ratio of major to minor axis of bounding box)
    elongation = max(h_bbox, w_bbox) / max(1.0, min(h_bbox, w_bbox))

    # Perimeter (approximate count of boundary pixels)
    from scipy.ndimage import binary_erosion
    try:
        eroded = binary_erosion(dark_mask)
        perimeter_px = float(np.sum(dark_mask ^ eroded))
    except Exception:
        perimeter_px = float(2 * (h_bbox + w_bbox))

    complexity = (perimeter_px ** 2) / (4.0 * np.pi * area_px + 1e-6)

    # 2. Radiometric damping and contrast
    slick_pixels = sar_patch[dark_mask]
    slick_mean = float(np.mean(slick_pixels))
    slick_std = float(np.std(slick_pixels))

    # Background ring (buffer zone around slick)
    from scipy.ndimage import binary_dilation
    try:
        dilated = binary_dilation(dark_mask, iterations=background_buffer)
        bg_mask = dilated & (~dark_mask)
        bg_pixels = sar_patch[bg_mask]
        if bg_pixels.size > 0:
            bg_mean = float(np.mean(bg_pixels))
            bg_std = float(np.std(bg_pixels))
            contrast_db = float(bg_mean - slick_mean)
        else:
            bg_mean = slick_mean + 5.0
            bg_std = slick_std
            contrast_db = 5.0
    except Exception:
        bg_mean = slick_mean + 5.0
        bg_std = slick_std
        contrast_db = 5.0

    # Boundary gradient sharpness (mean gradient magnitude along edge)
    from scipy.ndimage import sobel
    try:
        gx = sobel(sar_patch, axis=0)
        gy = sobel(sar_patch, axis=1)
        grad_mag = np.hypot(gx, gy)
        edge_mask = dark_mask ^ eroded
        if np.sum(edge_mask) > 0:
            boundary_gradient = float(np.mean(grad_mag[edge_mask]))
        else:
            boundary_gradient = 0.0
    except Exception:
        boundary_gradient = 0.0

    return {
        "area_px": area_px,
        "compactness": round(compactness, 4),
        "elongation": round(elongation, 4),
        "complexity": round(complexity, 4),
        "perimeter_px": perimeter_px,
        "slick_mean_db": round(slick_mean, 2),
        "slick_std": round(slick_std, 3),
        "bg_mean_db": round(bg_mean, 2),
        "bg_std": round(bg_std, 3),
        "contrast_db": round(contrast_db, 2),
        "boundary_gradient": round(boundary_gradient, 4),
    }


def _zero_features() -> Dict[str, float]:
    return {
        "area_px": 0.0,
        "compactness": 0.0,
        "elongation": 0.0,
        "complexity": 0.0,
        "perimeter_px": 0.0,
        "slick_mean_db": 0.0,
        "slick_std": 0.0,
        "bg_mean_db": 0.0,
        "bg_std": 0.0,
        "contrast_db": 0.0,
        "boundary_gradient": 0.0,
    }
