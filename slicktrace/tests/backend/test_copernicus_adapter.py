"""
SlickTrace v2 — Copernicus Data Space Sentinel Adapter Tests

Verifies:
- Strict credentials checking and CopernicusProviderUnavailable reporting
- Non-fabrication guarantee: never generates fake products
- OData filter builder for Sentinel-1 (polarization, GRD) and Sentinel-2 (cloud cover)
- Product caching and validation logic
"""
from datetime import datetime, timezone
from pathlib import Path
import pytest

from app.services.copernicus_adapter import (
    CopernicusDataSpaceAdapter,
    CopernicusProviderUnavailable,
)


def test_copernicus_availability_check_unconfigured():
    adapter = CopernicusDataSpaceAdapter(username="", password="")
    avail, reason = adapter.check_availability()
    assert avail is False
    assert "CDSE_USERNAME and CDSE_PASSWORD not configured" in reason


def test_copernicus_never_fabricates_when_unavailable():
    adapter = CopernicusDataSpaceAdapter(username="", password="")
    with pytest.raises(CopernicusProviderUnavailable) as exc:
        adapter.search_products(
            platform="SENTINEL-1",
            date_from=datetime(2023, 5, 1, tzinfo=timezone.utc),
            date_to=datetime(2023, 5, 15, tzinfo=timezone.utc),
            aoi_wkt="POLYGON((-91 27, -89 27, -89 29, -91 29, -91 27))",
        )
    assert "[UNAVAILABLE]" in str(exc.value)


def test_build_odata_filter_sentinel1():
    date_from = datetime(2023, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(2023, 5, 15, 23, 59, 59, tzinfo=timezone.utc)
    aoi_wkt = "POLYGON((-91 27, -89 27, -89 29, -91 29, -91 27))"

    filter_str = CopernicusDataSpaceAdapter.build_odata_filter(
        platform="SENTINEL-1",
        date_from=date_from,
        date_to=date_to,
        aoi_wkt=aoi_wkt,
        product_type="GRD",
        polarization="VV+VH",
    )

    assert "Collection/Name eq 'SENTINEL-1'" in filter_str
    assert "ContentDate/Start ge 2023-05-01T00:00:00.000Z" in filter_str
    assert "OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((-91 27, -89 27, -89 29, -91 29, -91 27))')" in filter_str
    assert "att/OData.CSC.StringAttribute/Value eq 'GRD'" in filter_str
    assert "att/OData.CSC.StringAttribute/Value eq 'VV&VH'" in filter_str


def test_build_odata_filter_sentinel2_with_cloud():
    date_from = datetime(2023, 6, 1, tzinfo=timezone.utc)
    date_to = datetime(2023, 6, 10, tzinfo=timezone.utc)

    filter_str = CopernicusDataSpaceAdapter.build_odata_filter(
        platform="SENTINEL-2",
        date_from=date_from,
        date_to=date_to,
        product_type="L2A",
        max_cloud_cover=15.0,
    )

    assert "Collection/Name eq 'SENTINEL-2'" in filter_str
    assert "att/OData.CSC.DoubleAttribute/Value le 15.0" in filter_str
    assert "att/OData.CSC.StringAttribute/Value eq 'L2A'" in filter_str


def test_validate_empty_file(tmp_path):
    empty_file = tmp_path / "empty_product.zip"
    empty_file.touch()

    adapter = CopernicusDataSpaceAdapter(username="test", password="pwd")
    res = adapter.validate_product(empty_file)
    assert res["valid"] is False
    assert "empty" in res["reason"].lower()


def test_validate_archive_product(tmp_path):
    sample_file = tmp_path / "S1A_IW_GRDH_SAMPLE.zip"
    sample_file.write_bytes(b"PK\x03\x04" + b"MockSentinelZipContent" * 100)

    adapter = CopernicusDataSpaceAdapter(username="test", password="pwd")
    res = adapter.validate_product(sample_file)

    assert res["valid"] is True
    assert res["details"]["is_archive"] is True
    assert "file_hash" in res["details"]
    assert len(res["details"]["file_hash"]) == 64
