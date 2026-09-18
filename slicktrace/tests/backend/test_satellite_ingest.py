"""
SlickTrace v2 — Satellite Evidence Ingestion Subsystem Tests

Verifies:
- Sentinel-1 SAR GRD and Sentinel-2 optical metadata heuristics
- Strict georeferencing validation: missing CRS marks geospatial attribution unavailable
- Strict timestamp extraction: missing timestamp marks temporal attribution unavailable
- Non-invention of metadata
- SHA-256 streaming checksum integrity
- Analysis-ready SAR backscatter calibration (linear to dB)
"""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
try:
    from rasterio.crs import CRS
    from rasterio.transform import from_origin
    RASTERIO_TEST_AVAILABLE = True
except ImportError:
    RASTERIO_TEST_AVAILABLE = False

from app.services.satellite_ingest import (
    SatelliteIngestService,
    compute_file_sha256_and_size,
)


def test_sentinel1_safe_filename_heuristics():
    # Standard Sentinel-1 IW GRD filename
    fn = "S1A_IW_GRDH_1SDV_20230515T061234_20230515T061300_048567_05D812_ABCD.SAFE"
    meta = SatelliteIngestService.parse_filename_heuristics(fn)

    assert meta["platform"] == "Sentinel-1A"
    assert "C-SAR" in meta["sensor"]
    assert meta["product_type"] == "GRDH"
    assert meta["polarization"] == "VV+VH"
    assert meta["acquisition_time"] == datetime(2023, 5, 15, 6, 12, 34, tzinfo=timezone.utc)


def test_sentinel2_safe_filename_heuristics():
    # Standard Sentinel-2 L2A filename
    fn = "S2B_MSIL2A_20230610T103021_N0509_R108_T32TMR_20230610T142010.SAFE"
    meta = SatelliteIngestService.parse_filename_heuristics(fn)

    assert meta["platform"] == "Sentinel-2B"
    assert meta["sensor"] == "MSI"
    assert meta["product_type"] == "MSIL2A"
    assert meta["acquisition_time"] == datetime(2023, 6, 10, 10, 30, 21, tzinfo=timezone.utc)


def test_unknown_filename_no_invention():
    # Random unbranded filename
    fn = "survey_scan_0049.tif"
    meta = SatelliteIngestService.parse_filename_heuristics(fn)

    assert meta["platform"] is None
    assert meta["sensor"] is None
    assert meta["product_type"] is None
    assert meta["polarization"] is None
    assert meta["acquisition_time"] is None


@pytest.mark.skipif(not RASTERIO_TEST_AVAILABLE, reason="rasterio required for CRS test")
def test_georeferencing_validation_with_valid_crs():
    crs_wgs84 = CRS.from_epsg(4326)
    transform = from_origin(-90.5, 28.5, 0.001, 0.001)

    (
        is_georef,
        geospatial_avail,
        crs_str,
        epsg,
        bbox,
        res_m,
        notes,
    ) = SatelliteIngestService.validate_georeferencing(
        crs_obj=crs_wgs84,
        transform=transform,
        width=1000,
        height=1000,
    )

    assert is_georef is True
    assert geospatial_avail is True
    assert epsg == 4326
    assert bbox is not None
    assert bbox.bounds[0] == pytest.approx(-90.5, rel=1e-3)
    assert bbox.bounds[2] == pytest.approx(-89.5, rel=1e-3)


def test_missing_crs_marks_geospatial_attribution_unavailable():
    # None CRS
    (
        is_georef,
        geospatial_avail,
        crs_str,
        epsg,
        bbox,
        res_m,
        notes,
    ) = SatelliteIngestService.validate_georeferencing(
        crs_obj=None,
        transform=None,
        width=512,
        height=512,
    )

    assert is_georef is False
    assert geospatial_avail is False
    assert bbox is None
    assert any("No Coordinate Reference System" in n for n in notes)


def test_missing_timestamp_marks_temporal_attribution_unavailable():
    tags = {"TIFFTAG_SOFTWARE": "CustomSARProcessor"}
    acq_time, temporal_avail = SatelliteIngestService.extract_acquisition_time(
        tags=tags,
        filename="unidentified_sar_scene.tif",
    )

    assert acq_time is None
    assert temporal_avail is False


def test_extracted_timestamp_from_tags():
    tags = {"TIFFTAG_DATETIME": "2024-04-12 14:30:00"}
    acq_time, temporal_avail = SatelliteIngestService.extract_acquisition_time(
        tags=tags,
        filename="unidentified_sar_scene.tif",
    )

    assert temporal_avail is True
    assert acq_time == datetime(2024, 4, 12, 14, 30, 0, tzinfo=timezone.utc)


def test_file_sha256_and_size(tmp_path):
    test_file = tmp_path / "satellite_test.tif"
    content = b"Simulated Sentinel-1 SAR GRD Binary Byte Stream" * 1024
    test_file.write_bytes(content)

    sha256, size = compute_file_sha256_and_size(test_file)

    expected_sha = hashlib.sha256(content).hexdigest()
    assert sha256 == expected_sha
    assert size == len(content)


@pytest.mark.skipif(not RASTERIO_TEST_AVAILABLE, reason="rasterio required for analysis-ready raster test")
def test_sar_analysis_ready_preprocessing(tmp_path):
    import rasterio

    raw_tif = tmp_path / "raw_sar.tif"
    out_tif = tmp_path / "analysis_ready.tif"

    # Create dummy georeferenced raster with positive amplitude DN values
    data = np.random.uniform(50.0, 500.0, (128, 128)).astype(np.float32)
    crs = CRS.from_epsg(4326)
    transform = from_origin(-89.0, 27.0, 0.001, 0.001)

    with rasterio.open(
        raw_tif,
        "w",
        driver="GTiff",
        height=128,
        width=128,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    # Preprocess
    result_path = SatelliteIngestService.preprocess_sar_to_analysis_ready(raw_tif, out_tif)
    assert result_path.exists()

    with rasterio.open(result_path) as src:
        ar_data = src.read(1)
        # Normalized values should be between 0.0 and 1.0 (excluding nodata)
        valid = ar_data != src.nodata
        assert valid.any()
        assert np.all(ar_data[valid] >= 0.0)
        assert np.all(ar_data[valid] <= 1.0)
        assert src.dtypes[0] == "float32"
