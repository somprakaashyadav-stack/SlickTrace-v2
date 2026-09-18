"""
SlickTrace v2 — Satellite Evidence Ingestion Subsystem

Implements forensic metadata extraction, CRS detection, georeferencing validation,
acquisition timestamp extraction, raster integrity validation, and analysis-ready
preprocessing for Sentinel-1 SAR GRD (primary) and Sentinel-2 optical imagery.

Strict Non-Invention Contract:
- If georeferencing / CRS is missing: mark geospatial_attribution_available = False.
- If acquisition time is missing: mark temporal_attribution_available = False.
- Never invent coordinates, timestamps, or sensor platforms.
"""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Spatial and raster libraries
try:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    from rasterio.warp import transform_bounds
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False

try:
    from shapely.geometry import Polygon, box, mapping
    from shapely.ops import transform as shapely_transform
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SatelliteIngestError(Exception):
    """Raised when critical raster corruption prevents file reading."""
    pass


def compute_file_sha256_and_size(path: Path) -> Tuple[str, int]:
    """Return (sha256_hex, total_size_bytes) reading in memory-safe 64KB chunks."""
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


class SatelliteIngestService:
    """
    Subsystem engine for satellite scene evidence ingestion and validation.
    """

    # Sentinel-1 SAFE standard naming regex
    # Example: S1A_IW_GRDH_1SDV_20230515T061234_20230515T061300_048567_05D812_ABCD.SAFE
    S1_PATTERN = re.compile(
        r"^(S1[AB])_([A-Z0-9]{2})_([A-Z]{3,4})_([0-9A-Z]{4})_([0-9]{8}T[0-9]{6})_([0-9]{8}T[0-9]{6})",
        re.IGNORECASE,
    )

    # Sentinel-2 SAFE standard naming regex
    # Example: S2A_MSIL2A_20230515T103021_N0509_R108_T32TMR_20230515T142010.SAFE
    S2_PATTERN = re.compile(
        r"^(S2[AB])_([A-Z0-9]{6})_([0-9]{8}T[0-9]{6})",
        re.IGNORECASE,
    )

    @classmethod
    def parse_filename_heuristics(cls, filename: str) -> Dict[str, Any]:
        """
        Extract platform, sensor, product type, polarization, and timestamp
        from standard ESA naming conventions if present.
        Does NOT invent if unrecognized.
        """
        info: Dict[str, Any] = {
            "platform": None,
            "sensor": None,
            "product_type": None,
            "polarization": None,
            "acquisition_time": None,
        }

        # Check Sentinel-1 SAR
        s1_match = cls.S1_PATTERN.search(filename)
        if s1_match:
            sat_id, mode, ptype, pol_code, start_time, _ = s1_match.groups()
            info["platform"] = f"Sentinel-1{sat_id[-1].upper()}"
            info["sensor"] = f"C-SAR ({mode.upper()})"
            info["product_type"] = ptype.upper()

            # Polarization mapping
            pol_map = {
                "1SDV": "VV+VH",
                "1SDH": "HH+HV",
                "1SSV": "VV",
                "1SSH": "HH",
            }
            info["polarization"] = pol_map.get(pol_code.upper(), pol_code.upper())

            try:
                dt = datetime.strptime(start_time, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                info["acquisition_time"] = dt
            except ValueError:
                pass
            return info

        # Check Sentinel-2 Optical
        s2_match = cls.S2_PATTERN.search(filename)
        if s2_match:
            sat_id, ptype, start_time = s2_match.groups()
            info["platform"] = f"Sentinel-2{sat_id[-1].upper()}"
            info["sensor"] = "MSI"
            info["product_type"] = ptype.upper()
            try:
                dt = datetime.strptime(start_time, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                info["acquisition_time"] = dt
            except ValueError:
                pass
            return info

        # Check generic keywords
        fn_upper = filename.upper()
        if "SENTINEL-1" in fn_upper or "S1" in fn_upper:
            info["platform"] = "Sentinel-1"
            info["sensor"] = "C-SAR"
        elif "SENTINEL-2" in fn_upper or "S2" in fn_upper:
            info["platform"] = "Sentinel-2"
            info["sensor"] = "MSI"

        if "GRD" in fn_upper:
            info["product_type"] = "GRD"
        elif "COG" in fn_upper:
            info["product_type"] = "COG"

        if "VV" in fn_upper and "VH" in fn_upper:
            info["polarization"] = "VV+VH"
        elif "_VV" in fn_upper or "VV_" in fn_upper:
            info["polarization"] = "VV"
        elif "_VH" in fn_upper or "VH_" in fn_upper:
            info["polarization"] = "VH"

        return info

    @classmethod
    def extract_acquisition_time(
        cls,
        tags: Dict[str, Any],
        filename: str,
    ) -> Tuple[Optional[datetime], bool]:
        """
        Extract timestamp from TIFF/GDAL metadata tags or filename.
        Returns (acquisition_time, temporal_attribution_available).
        """
        # 1. Look in tags
        candidates = [
            tags.get("TIFFTAG_DATETIME"),
            tags.get("ACQUISITION_DATETIME"),
            tags.get("acquisition_time"),
            tags.get("IMAGE_DATETIME"),
            tags.get("START_TIME"),
        ]

        for cand in candidates:
            if not cand or not isinstance(cand, str):
                continue
            cleaned = cand.strip().replace("Z", "+00:00")
            # Try ISO formats
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y:%m:%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ):
                try:
                    dt = datetime.strptime(cleaned.split("+")[0], fmt).replace(tzinfo=timezone.utc)
                    return dt, True
                except ValueError:
                    continue

        # 2. Look in filename heuristics
        heuristics = cls.parse_filename_heuristics(filename)
        if heuristics["acquisition_time"] is not None:
            return heuristics["acquisition_time"], True

        # Timestamp missing — strict contract: do NOT invent
        return None, False

    @classmethod
    def validate_georeferencing(
        cls,
        crs_obj: Any,
        transform: Any,
        width: int,
        height: int,
    ) -> Tuple[bool, bool, Optional[str], Optional[int], Optional[Polygon], Optional[Tuple[float, float]], List[str]]:
        """
        Validates CRS and affine transformation. Computes WGS84 bounding box polygon.
        Returns:
            is_georeferenced (bool)
            geospatial_attribution_available (bool)
            crs_wkt_or_proj (str or None)
            crs_epsg (int or None)
            bbox_wgs84 (Shapely Polygon or None)
            (res_x, res_y) in meters or None
            validation_notes (list of str)
        """
        notes: List[str] = []

        if crs_obj is None or not crs_obj:
            notes.append("No Coordinate Reference System (CRS) detected in raster metadata.")
            return False, False, None, None, None, None, notes

        # Check affine transform
        if transform is None:
            notes.append("Missing affine geotransform matrix.")
            return False, False, None, None, None, None, notes

        # Detect default / identity affine transform (which means no real spatial anchoring)
        if (
            isinstance(transform, Affine)
            and transform.a == 1.0
            and transform.b == 0.0
            and transform.c == 0.0
            and transform.d == 0.0
            and transform.e == 1.0
            and transform.f == 0.0
        ):
            notes.append("Raster transform is default identity matrix (0,0); no real spatial anchoring.")
            return False, False, None, None, None, None, notes

        crs_str = str(crs_obj)
        epsg_code = None
        try:
            if hasattr(crs_obj, "to_epsg"):
                epsg_code = crs_obj.to_epsg()
        except Exception:
            pass

        # Calculate bounding box in native coordinates
        try:
            x_min, y_max = transform * (0, 0)
            x_max, y_min = transform * (width, height)
            if x_min > x_max:
                x_min, x_max = x_max, x_min
            if y_min > y_max:
                y_min, y_max = y_max, y_min

            res_x = abs(transform.a)
            res_y = abs(transform.e)

            # Convert to meters if degrees (approximate for EPSG:4326)
            if epsg_code == 4326 or "4326" in crs_str:
                res_x_m = res_x * 111320.0
                res_y_m = res_y * 111320.0
            else:
                res_x_m = res_x
                res_y_m = res_y

            # Reproject to WGS84 (EPSG:4326) for standardized storage
            if epsg_code == 4326:
                wgs84_poly = box(x_min, y_min, x_max, y_max)
            else:
                if PYPROJ_AVAILABLE:
                    transformer = Transformer.from_crs(crs_obj, "EPSG:4326", always_xy=True)
                    lon_min, lat_min = transformer.transform(x_min, y_min)
                    lon_max, lat_max = transformer.transform(x_max, y_max)
                    wgs84_poly = box(
                        min(lon_min, lon_max),
                        min(lat_min, lat_max),
                        max(lon_min, lon_max),
                        max(lat_min, lat_max),
                    )
                else:
                    wgs84_poly = box(x_min, y_min, x_max, y_max)

            return (
                True,
                True,
                crs_str,
                epsg_code,
                wgs84_poly,
                (round(float(res_x_m), 2), round(float(res_y_m), 2)),
                notes,
            )

        except Exception as e:
            notes.append(f"Georeferencing projection failed: {e}")
            return True, False, crs_str, epsg_code, None, None, notes

    @classmethod
    def preprocess_sar_to_analysis_ready(
        cls,
        input_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Processes Sentinel-1 SAR GRD to analysis-ready backscatter (dB):
        - Radiometric calibration: $10 \\cdot \\log_{10}(\\text{DN}^2 + 10^{-7})$
        - Spatial speckle filter (3x3 median)
        - Robust 1st-99th percentile normalization to float32
        - Output written as Cloud-Optimized GeoTIFF with preserved georeferencing
        """
        if not RASTERIO_AVAILABLE:
            raise SatelliteIngestError("Rasterio required for analysis-ready raster generation")

        with rasterio.open(input_path) as src:
            profile = src.profile.copy()
            arr = src.read(1).astype(np.float32)
            nodata = src.nodata

        # Mask invalid / non-positive values
        if nodata is not None:
            valid_mask = arr != nodata
        else:
            valid_mask = arr > 0

        # Linear amplitude to dB
        arr_safe = np.where(valid_mask, arr, np.nan)
        arr_db = 10.0 * np.log10(np.square(arr_safe) + 1e-7)

        # Speckle reduction via median filter
        arr_filtered = np.nan_to_num(arr_db, nan=-35.0)
        if CV2_AVAILABLE:
            # OpenCV median blur requires uint8 or float32 single channel
            arr_filtered = cv2.medianBlur(arr_filtered, 3)
        else:
            from scipy.ndimage import median_filter
            arr_filtered = median_filter(arr_filtered, size=3)

        # Robust normalisation
        finite_vals = arr_filtered[valid_mask] if valid_mask.any() else arr_filtered
        if finite_vals.size > 0:
            p1, p99 = np.percentile(finite_vals, [1, 99])
            norm = np.clip((arr_filtered - p1) / (p99 - p1 + 1e-6), 0.0, 1.0)
        else:
            norm = np.zeros_like(arr_filtered)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        profile.update(
            dtype="float32",
            count=1,
            nodata=-9999.0,
            driver="GTiff",
            tiled=True,
            compress="deflate",
        )

        norm[~valid_mask] = -9999.0
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(norm.astype(np.float32), 1)

        return output_path

    @classmethod
    def inspect_and_validate(
        cls,
        file_path: Path,
        original_filename: str,
    ) -> Dict[str, Any]:
        """
        Comprehensive inspection pipeline for uploaded satellite evidence.
        """
        if not file_path.exists():
            raise SatelliteIngestError(f"File not found: {file_path}")

        file_hash, size_bytes = compute_file_sha256_and_size(file_path)

        if not RASTERIO_AVAILABLE:
            raise SatelliteIngestError("Rasterio is required to inspect satellite raster evidence.")

        validation_notes: List[str] = []

        try:
            with rasterio.open(file_path) as src:
                width = src.width
                height = src.height
                bands = src.count
                dtype_str = str(src.dtypes[0])
                nodata = src.nodata
                crs_obj = src.crs
                transform = src.transform
                raw_tags = dict(src.tags())
                raw_tags.update(dict(src.tags(ns="ENVI") or {}))
        except Exception as e:
            raise SatelliteIngestError(f"Raster validation failed: corrupted or unsupported format: {e}")

        # Dimension validation
        if width <= 0 or height <= 0 or bands <= 0:
            raise SatelliteIngestError(f"Invalid raster dimensions: {width}x{height}, {bands} bands")

        # Filename heuristics
        fn_meta = cls.parse_filename_heuristics(original_filename)
        platform = raw_tags.get("PLATFORM") or raw_tags.get("MISSION_ID") or fn_meta["platform"]
        sensor = raw_tags.get("SENSOR") or raw_tags.get("INSTRUMENT_ID") or fn_meta["sensor"]
        product_type = raw_tags.get("PRODUCT_TYPE") or fn_meta["product_type"] or "GeoTIFF"
        polarization = raw_tags.get("POLARIZATION") or fn_meta["polarization"]

        # Acquisition timestamp extraction
        acq_time, temporal_available = cls.extract_acquisition_time(raw_tags, original_filename)
        if not temporal_available:
            validation_notes.append("Acquisition timestamp not present: temporal attribution unavailable.")

        # Georeferencing & CRS validation
        (
            is_georef,
            geospatial_available,
            crs_str,
            crs_epsg,
            bbox_wgs84,
            res_m,
            geo_notes,
        ) = cls.validate_georeferencing(crs_obj, transform, width, height)

        validation_notes.extend(geo_notes)
        if not geospatial_available:
            validation_notes.append("Spatial georeferencing invalid or unanchored: geospatial attribution unavailable.")

        res_x_m = res_m[0] if res_m else None
        res_y_m = res_m[1] if res_m else None

        return {
            "filename": original_filename,
            "file_hash": file_hash,
            "size_bytes": size_bytes,
            "platform": platform,
            "sensor": sensor,
            "product_type": product_type,
            "polarization": polarization,
            "acquisition_time": acq_time,
            "temporal_attribution_available": temporal_available,
            "crs": crs_str,
            "crs_epsg": crs_epsg,
            "is_georeferenced": is_georef,
            "geospatial_attribution_available": geospatial_available,
            "bbox_polygon": bbox_wgs84,
            "resolution_x_m": res_x_m,
            "resolution_y_m": res_y_m,
            "width": width,
            "height": height,
            "bands": bands,
            "nodata_value": float(nodata) if nodata is not None else None,
            "dtype": dtype_str,
            "validation_notes": validation_notes,
            "raw_metadata": raw_tags,
        }
