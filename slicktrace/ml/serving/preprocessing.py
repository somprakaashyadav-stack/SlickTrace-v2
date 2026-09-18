"""
SlickTrace v2 — SAR preprocessing for ML inference.

Handles GeoTIFF/COG loading, normalisation, band extraction,
and conversion of probability masks to GeoJSON polygons.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np

try:
    import rasterio
    import rasterio.features
    from rasterio.transform import Affine
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


class PreprocessingError(Exception):
    pass


def load_sar_geotiff(path: Path, band: int = 1) -> Tuple[np.ndarray, Dict]:
    """
    Load a SAR GeoTIFF and return normalised array + metadata.

    Args:
        path: Path to GeoTIFF file (Sentinel-1 IW GRD or similar)
        band: Band index to read (1-indexed), default 1 (VV)

    Returns:
        array: np.ndarray (H, W) float32, normalised 0-1 (dB scale, 2-98 percentile)
        meta: dict with crs, transform (list), bounds, shape, nodata

    Raises:
        PreprocessingError: if file not found or cannot be parsed
    """
    if not RASTERIO_AVAILABLE:
        raise PreprocessingError("rasterio not installed. pip install rasterio")
    if not path.exists():
        raise PreprocessingError(f"File not found: {path}")

    try:
        with rasterio.open(path) as src:
            arr = src.read(band).astype(np.float32)
            meta = {
                "crs": str(src.crs),
                "transform": list(src.transform),
                "bounds": list(src.bounds),
                "shape": (src.height, src.width),
                "nodata": src.nodata,
            }
    except Exception as e:
        raise PreprocessingError(f"Failed to read GeoTIFF: {e}")

    # Replace nodata / non-positive values with NaN before dB conversion
    arr = np.where(arr <= 0, np.nan, arr)

    # Convert amplitude DN to dB (Sentinel-1 stores linear amplitude)
    arr_db = 10.0 * np.log10(arr + 1e-10)

    # Robust normalisation to 0-1 using 2nd–98th percentile
    p2, p98 = np.nanpercentile(arr_db, [2, 98])
    arr_norm = np.clip((arr_db - p2) / (p98 - p2 + 1e-9), 0.0, 1.0)
    arr_norm = np.nan_to_num(arr_norm, nan=0.0)

    return arr_norm.astype(np.float32), meta


def mask_to_geojson_polygon(
    mask: np.ndarray,
    transform: list,
    crs: str,
    threshold: float = 0.5,
) -> dict:
    """
    Convert a float probability mask to a GeoJSON Feature (MultiPolygon).

    Args:
        mask: (H, W) float32 0-1 probability map
        transform: rasterio affine transform as 6-element list [a, b, c, d, e, f]
        crs: CRS string (e.g. "EPSG:4326")
        threshold: binarisation threshold

    Returns:
        GeoJSON Feature dict with geometry (MultiPolygon or null) and area_km2 property
    """
    if not RASTERIO_AVAILABLE or not SHAPELY_AVAILABLE:
        raise PreprocessingError("rasterio and shapely required for polygon extraction")

    binary = (mask >= threshold).astype(np.uint8)
    if binary.sum() == 0:
        return {"type": "Feature", "geometry": None, "properties": {"area_km2": 0.0}}

    aff = Affine(*transform[:6])
    shapes_gen = rasterio.features.shapes(binary, mask=binary, transform=aff)
    polys = [shape(geom) for geom, val in shapes_gen if val == 1]

    if not polys:
        return {"type": "Feature", "geometry": None, "properties": {"area_km2": 0.0}}

    merged = unary_union(polys)

    # Estimate area in km² (approximation: 1 degree ≈ 111 km at equator)
    # For production: use equal-area projection
    area_km2 = round(merged.area * 111.0 * 111.0, 4)

    return {
        "type": "Feature",
        "geometry": mapping(merged),
        "properties": {"area_km2": area_km2},
    }
