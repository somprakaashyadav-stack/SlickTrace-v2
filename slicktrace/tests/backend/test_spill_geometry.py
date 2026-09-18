"""
SlickTrace v2 — Unit Tests for Geospatial Spill Geometry Generation Engine

Verifies:
1. determine_utm_crs() accurately resolves UTM EPSG zones in North & South hemispheres.
2. clean_binary_mask() applies morphological closing and removes isolated noise pixels.
3. Empty mask handling returns safe null geometry and zeroed metrics.
4. Metric area & perimeter are calculated in projected UTM CRS (not raw degree coordinates).
5. Geometry simplification & validity repair maintain topological integrity.
"""
import math
import numpy as np
import pytest

from app.services.spill_geometry_service import (
    determine_utm_crs,
    clean_binary_mask,
    SpillGeometryEngine,
    RASTERIO_AVAILABLE,
    PYPROJ_AVAILABLE,
)


def test_determine_utm_crs_north_hemisphere():
    """Verify UTM zone calculation for Northern Hemisphere locations."""
    # Gulf of Mexico (~ -90.5, 27.5) -> UTM zone 15N
    epsg_gom, desc_gom = determine_utm_crs(-90.5, 27.5)
    assert epsg_gom == 32615
    assert "UTM zone 15N" in desc_gom

    # North Sea (~ 3.0, 56.0) -> UTM zone 31N
    epsg_ns, desc_ns = determine_utm_crs(3.0, 56.0)
    assert epsg_ns == 32631
    assert "UTM zone 31N" in desc_ns

    # Prime Meridian near London (~ -0.1, 51.5) -> UTM zone 30N
    epsg_uk, desc_uk = determine_utm_crs(-0.1, 51.5)
    assert epsg_uk == 32630
    assert "UTM zone 30N" in desc_uk


def test_determine_utm_crs_south_hemisphere():
    """Verify UTM zone calculation for Southern Hemisphere locations."""
    # Brazil offshore (~ -43.0, -22.0) -> UTM zone 23S (32700 + 23 = 32723)
    epsg_br, desc_br = determine_utm_crs(-43.0, -22.0)
    assert epsg_br == 32723
    assert "UTM zone 23S" in desc_br

    # Cape of Good Hope (~ 18.5, -34.5) -> UTM zone 34S
    epsg_sa, desc_sa = determine_utm_crs(18.5, -34.5)
    assert epsg_sa == 32734
    assert "UTM zone 34S" in desc_sa


def test_clean_binary_mask_pinholes_and_noise():
    """Verify morphological cleaning fills small pinholes and removes tiny noise artifacts."""
    mask = np.zeros((100, 100), dtype=np.uint8)

    # Create a solid 30x30 square slick with a 1-pixel pinhole inside
    mask[20:50, 20:50] = 1
    mask[35, 35] = 0  # pinhole hole

    # Create isolated 1-pixel false-alarm noise spikes
    mask[5, 5] = 1
    mask[80, 80] = 1

    cleaned = clean_binary_mask(mask, close_kernel_size=5, open_kernel_size=3, min_component_pixels=10)

    # Pinhole should be filled
    assert cleaned[35, 35] == 1, "Pinhole inside slick should be morphologically closed"

    # Isolated noise spikes should be removed
    assert cleaned[5, 5] == 0, "Single-pixel noise spike at (5, 5) should be removed"
    assert cleaned[80, 80] == 0, "Single-pixel noise spike at (80, 80) should be removed"

    # Main slick mass should be preserved
    assert np.sum(cleaned[20:50, 20:50]) >= 850


def test_generate_spill_geometry_empty_mask():
    """Verify empty mask returns graceful empty geometry."""
    mask = np.zeros((128, 128), dtype=np.uint8)
    result = SpillGeometryEngine.generate_spill_geometry(mask)

    assert result["area_km2"] == 0.0
    assert result["perimeter_km"] == 0.0
    assert result["geojson_polygon"] is None
    assert result["geometry_quality"]["validity"] == "empty"


def test_generate_spill_geometry_pixel_space():
    """Verify fallback pixel space geometry calculation when unprojected."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    # 20x20 block = 400 pixels
    mask[20:40, 20:40] = 1

    result = SpillGeometryEngine.generate_spill_geometry(mask, transform=None, pixel_size_m=10.0)

    assert result["area_km2"] > 0
    # 400 pixels * (10m * 10m) = 40,000 m2 = 0.04 km2
    assert pytest.approx(result["area_km2"], abs=0.005) == 0.04
    assert result["perimeter_km"] > 0
    assert result["geojson_polygon"] is not None
    assert result["geometry_quality"]["validity"] in ("valid", "repaired")


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="Rasterio not installed in test environment")
def test_generate_spill_geometry_georeferenced_utm_metric_calculation():
    """
    CRITICAL CONTRACT TEST:
    Calculate area in an appropriate projected CRS (UTM), not raw degrees!
    """
    from rasterio.transform import from_bounds

    mask = np.zeros((500, 500), dtype=np.uint8)
    # 100x100 pixel patch in center
    mask[200:300, 200:300] = 1

    # GeoTIFF bounds covering ~0.5 deg x 0.5 deg near Gulf of Mexico (-90.0, 28.0)
    # At 28°N, 1 deg ~ 111 km lat, ~98 km lon.
    # 0.5 deg span ~ 50 km. 500 pixels => ~100m / pixel ground resolution.
    # 100x100 pixels => ~10 km x 10 km = ~100 km2.
    transform = from_bounds(-90.5, 27.5, -90.0, 28.0, 500, 500)

    result = SpillGeometryEngine.generate_spill_geometry(
        mask=mask,
        transform=transform,
        simplification_tolerance=0.0001,
    )

    # 1. Projected CRS must be set to UTM zone 15N or 16N
    assert "UTM" in result["projected_crs"]
    assert "EPSG:32615" in result["projected_crs"] or "EPSG:32616" in result["projected_crs"]

    # 2. Area must be in true km2 (approx ~95 - 105 km2), NOT raw degrees squared (~0.01)
    assert result["area_km2"] > 10.0, (
        f"Area {result['area_km2']} km2 is suspiciously small! "
        "Must be computed in projected metric CRS, not raw degrees!"
    )
    assert 70.0 <= result["area_km2"] <= 130.0

    # 3. Perimeter must be in true km (~35 - 45 km), NOT raw degrees (~0.4)
    assert result["perimeter_km"] > 10.0
    assert 30.0 <= result["perimeter_km"] <= 50.0

    # 4. Centroid must be in WGS84 coordinates near -90.25, 27.75
    assert -90.5 <= result["centroid_lon"] <= -90.0
    assert 27.5 <= result["centroid_lat"] <= 28.0

    # 5. Bounding box must be [min_lon, min_lat, max_lon, max_lat]
    bbox = result["bbox"]
    assert len(bbox) == 4
    assert bbox[0] < bbox[2]  # min_lon < max_lon
    assert bbox[1] < bbox[3]  # min_lat < max_lat

    # 6. Quality indicators
    quality = result["geometry_quality"]
    assert quality["validity"] in ("valid", "repaired")
    assert quality["vertex_count"] >= 4


def test_generate_spill_geometry_projected_utm_metric_calculation_portable():
    """
    CRITICAL CONTRACT TEST (portable without external GDAL/Rasterio dependency):
    Verifies that with any affine transform, area is calculated in UTM km2, NOT raw degrees.
    """
    class MockAffine:
        """Simulates Affine transform from raster bounds."""
        def __init__(self, x_min, y_min, x_max, y_max, width, height):
            self.res_x = (x_max - x_min) / width
            self.res_y = (y_max - y_min) / height
            self.x_min = x_min
            self.y_max = y_max

        def __mul__(self, pt):
            col, row = pt
            # GeoTIFF raster convention: top-to-bottom
            return (self.x_min + col * self.res_x, self.y_max - row * self.res_y)

    mask = np.zeros((500, 500), dtype=np.uint8)
    # 100x100 pixel block
    mask[200:300, 200:300] = 1

    # Bounds: -90.5 to -90.0 Lon, 27.5 to 28.0 Lat (Gulf of Mexico)
    transform = MockAffine(-90.5, 27.5, -90.0, 28.0, 500, 500)

    result = SpillGeometryEngine.generate_spill_geometry(
        mask=mask,
        transform=transform,
        simplification_tolerance=0.0001,
    )

    # 1. Projected CRS must specify UTM
    assert "UTM" in result["projected_crs"]
    assert "EPSG:32615" in result["projected_crs"] or "EPSG:32616" in result["projected_crs"]

    # 2. Area must be in km2 (~80-120 km2 for 10km x 10km), NOT raw degrees squared (~0.01)
    assert result["area_km2"] > 10.0, (
        f"Area {result['area_km2']} km2 is too small! Must be projected metric area."
    )
    assert 70.0 <= result["area_km2"] <= 130.0

    # 3. Perimeter must be in km
    assert result["perimeter_km"] > 10.0
    assert 25.0 <= result["perimeter_km"] <= 55.0

    # 4. Centroid within Gulf of Mexico AOI
    assert -90.5 <= result["centroid_lon"] <= -90.0
    assert 27.5 <= result["centroid_lat"] <= 28.0

    # 5. Bounding box coordinates valid
    bbox = result["bbox"]
    assert bbox[0] < bbox[2]
    assert bbox[1] < bbox[3]

