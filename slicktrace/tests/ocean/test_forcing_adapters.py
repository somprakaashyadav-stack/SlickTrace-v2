"""
SlickTrace v2 — Unit Tests for Environmental Forcing Adapters

Verifies:
1. AOI parsing from tuples, lists, dicts, and GeoJSON.
2. NormalizedForcingData contract: timestamp, lat, lon, u, v, source, dataset_version, resolution.
3. Vector mathematics: magnitude (speed) and direction.
4. Caching subsystem: deterministic keys, storage, and retrieval.
5. Strict Real-Data Contract:
   - WindProvider raises OceanDataUnavailable when CDS_KEY is missing (never substitutes synthetic data).
   - CurrentProvider raises OceanDataUnavailable when CMEMS credentials missing (unless allow_fallback is explicitly True).
   - Provenance records real source (e.g. HYCOM) when fallback is used and never claims to be CMEMS.
6. Generic reader normalization from gridded datasets.
"""
import math
import shutil
import tempfile
from pathlib import Path
import numpy as np
import pytest

from ocean.forcing.models import (
    AOI,
    ForcingProvenance,
    NormalizedForcingData,
    parse_aoi,
)
from ocean.forcing.cache import ForcingCacheManager
from ocean.forcing.generic_reader import GenericForcingReader
from ocean.forcing.providers import (
    CurrentProvider,
    WaveProvider,
    WindProvider,
)
from ocean.readers.base import OceanDataUnavailable


def test_aoi_parsing_and_validation():
    """Verify AOI parsing from multiple input formats."""
    # From tuple
    a1 = parse_aoi((-90.5, 27.5, -89.5, 28.5))
    assert a1.lon_min == -90.5
    assert a1.lat_max == 28.5

    # From dict with lon_min/lat_min
    a2 = parse_aoi({"lon_min": -10.0, "lat_min": 50.0, "lon_max": -5.0, "lat_max": 55.0})
    assert a2.lon_min == -10.0

    # From dict with min_lon/min_lat
    a3 = parse_aoi({"min_lon": 0.0, "min_lat": 10.0, "max_lon": 5.0, "max_lat": 15.0})
    assert a3.lon_max == 5.0

    # From GeoJSON polygon
    geojson_poly = {
        "type": "Polygon",
        "coordinates": [[
            [-90.0, 27.0],
            [-89.0, 27.0],
            [-89.0, 28.0],
            [-90.0, 28.0],
            [-90.0, 27.0],
        ]],
    }
    a4 = parse_aoi(geojson_poly)
    assert a4.lon_min == -90.0
    assert a4.lon_max == -89.0
    assert a4.lat_min == 27.0
    assert a4.lat_max == 28.0

    # Invalid coordinates raise ValueError
    with pytest.raises(ValueError):
        AOI(lon_min=10.0, lat_min=20.0, lon_max=5.0, lat_max=25.0)  # min > max


def test_normalized_forcing_data_contract():
    """Verify NormalizedForcingData fields, array shapes, and utility methods."""
    lats = [27.0, 27.5, 28.0]
    lons = [-90.5, -90.0, -89.5]
    times = ["2026-09-17T00:00:00Z", "2026-09-17T01:00:00Z"]

    # u = 3.0 m/s, v = 4.0 m/s -> magnitude = 5.0 m/s
    u = np.full((2, 3, 3), 3.0, dtype=np.float32)
    v = np.full((2, 3, 3), 4.0, dtype=np.float32)

    prov = ForcingProvenance(
        source_name="ERA5 (Copernicus CDS)",
        dataset_id="reanalysis-era5-single-levels",
        dataset_version="ERA5_hourly_10m_v1",
        source_url="https://cds.climate.copernicus.eu/api/v2",
        raw_file_sha256="abc123def456",
        spatial_bounds={"lon_min": -90.5, "lat_min": 27.0, "lon_max": -89.5, "lat_max": 28.0},
        time_range={"start": times[0], "end": times[1]},
        execution_duration_sec=1.2,
    )

    data = NormalizedForcingData(
        variable_type="wind",
        timestamp=times,
        latitude=lats,
        longitude=lons,
        u=u,
        v=v,
        source="ERA5",
        dataset_version="ERA5_hourly_10m_v1",
        resolution="0.25 deg, 1h",
        provenance=prov,
    )

    # Magnitude calculation
    mag = data.magnitude()
    assert np.allclose(mag, 5.0)

    # Direction calculation: arctan2(3, 4) in degrees ~ 36.87°
    dir_deg = data.direction()
    assert pytest.approx(dir_deg[0, 0, 0], abs=0.1) == 36.87

    # Nearest-neighbor point sampling
    u_pt, v_pt, speed_pt = data.get_point(lat=27.4, lon=-90.1, time_idx=0)
    assert u_pt == 3.0
    assert v_pt == 4.0
    assert pytest.approx(speed_pt, abs=0.01) == 5.0

    # Serialization
    d = data.to_dict()
    assert d["variable_type"] == "wind"
    assert d["source"] == "ERA5"
    assert d["dataset_version"] == "ERA5_hourly_10m_v1"
    assert d["resolution"] == "0.25 deg, 1h"
    assert d["speed_mean_ms"] == 5.0
    assert d["provenance"]["raw_file_sha256"] == "abc123def456"


def test_forcing_cache_determinism_and_hit():
    """Verify deterministic cache keying and roundtrip storage in ForcingCacheManager."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        cache = ForcingCacheManager(cache_dir=temp_dir)
        aoi = AOI(-90.5, 27.5, -89.5, 28.5)
        start = "2026-09-17T00:00:00Z"
        end = "2026-09-17T12:00:00Z"

        key1 = cache.compute_cache_key("wind", "ERA5", aoi, start, end)
        key2 = cache.compute_cache_key("wind", "ERA5", aoi, start, end)
        assert key1 == key2, "Cache key generation must be strictly deterministic"

        assert not cache.has(key1)

        # Create sample normalized data
        sample = NormalizedForcingData(
            variable_type="wind",
            timestamp=[start],
            latitude=[27.5, 28.5],
            longitude=[-90.5, -89.5],
            u=np.array([[2.5, 3.0], [2.0, 3.5]]),
            v=np.array([[1.0, 1.5], [1.2, 1.8]]),
            source="ERA5",
            dataset_version="ERA5_v1",
            resolution="0.25 deg, 1h",
        )

        cache.store_normalized(key1, sample)
        assert cache.has(key1)

        loaded = cache.get_normalized(key1)
        assert loaded is not None
        assert loaded.source == "ERA5"
        assert np.allclose(loaded.u, sample.u)
        assert np.allclose(loaded.v, sample.v)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_wind_provider_unconfigured_era5_raises_unavailable(monkeypatch):
    """
    CRITICAL CONTRACT TEST:
    WindProvider must never silently substitute fake wind when CDS_KEY is missing.
    """
    monkeypatch.setenv("CDS_KEY", "")
    wp = WindProvider()
    aoi = AOI(-90.5, 27.5, -89.5, 28.5)

    with pytest.raises(OceanDataUnavailable) as exc_info:
        wp.get_wind(aoi, "2026-09-17T00:00:00Z", "2026-09-17T12:00:00Z", use_cache=False)

    err = str(exc_info.value)
    assert "[UNAVAILABLE]" in err
    assert "CDS_KEY not configured" in err
    assert "https://cds.climate.copernicus.eu/" in err


def test_current_provider_unconfigured_cmems_raises_unavailable(monkeypatch):
    """
    CRITICAL CONTRACT TEST:
    CurrentProvider must never silently substitute fake currents when CMEMS credentials missing.
    """
    monkeypatch.setenv("CMEMS_USERNAME", "")
    monkeypatch.setenv("CMEMS_PASSWORD", "")
    cp = CurrentProvider()
    aoi = AOI(-90.5, 27.5, -89.5, 28.5)

    with pytest.raises(OceanDataUnavailable) as exc_info:
        cp.get_currents(aoi, "2026-09-17T00:00:00Z", "2026-09-17T12:00:00Z", allow_fallback=False, use_cache=False)

    err = str(exc_info.value)
    assert "[UNAVAILABLE]" in err
    assert "CMEMS_USERNAME" in err
    assert "https://marine.copernicus.eu/" in err


def test_wave_provider_unconfigured_raises_unavailable(monkeypatch):
    """
    CRITICAL CONTRACT TEST:
    WaveProvider must never silently substitute fake wave data.
    """
    monkeypatch.setenv("CMEMS_USERNAME", "")
    monkeypatch.setenv("CMEMS_PASSWORD", "")
    wavp = WaveProvider()
    aoi = AOI(-90.5, 27.5, -89.5, 28.5)

    with pytest.raises(OceanDataUnavailable) as exc_info:
        wavp.get_waves(aoi, "2026-09-17T00:00:00Z", "2026-09-17T12:00:00Z", use_cache=False)

    err = str(exc_info.value)
    assert "[UNAVAILABLE]" in err
    assert "https://marine.copernicus.eu/" in err


def test_generic_forcing_reader_normalizes_mock_dataset():
    """
    Tests that GenericForcingReader correctly identifies lat, lon, time, and u/v components
    across standard meteorological coordinate naming conventions.
    """
    class MockVariable:
        def __init__(self, data, units=""):
            self._data = np.array(data)
            self.units = units

        def __getitem__(self, item):
            return self._data[item]

        def __len__(self):
            return len(self._data)

    class MockDataset:
        def __init__(self, var_dict):
            self.variables = {k: MockVariable(v) for k, v in var_dict.items()}

    # Dataset with ERA5 convention: latitude, longitude, time, u10, v10
    raw_dict = {
        "latitude": [27.0, 28.0],
        "longitude": [-90.0, -89.0],
        "time": [0, 1],
        "u10": np.array([[[1.5, 2.0], [1.8, 2.2]], [[2.0, 2.5], [2.2, 2.8]]]),
        "v10": np.array([[[3.0, 3.5], [3.2, 3.8]], [[3.5, 4.0], [3.8, 4.2]]]),
    }

    mock_ds = MockDataset(raw_dict)
    normalized = GenericForcingReader.parse_netcdf_dataset(
        nc_dataset=mock_ds,
        variable_type="wind",
        source="ERA5",
        dataset_version="ERA5_hourly_10m_v1",
        resolution="0.25 deg, 1h",
    )

    assert normalized.variable_type == "wind"
    assert normalized.source == "ERA5"
    assert len(normalized.latitude) == 2
    assert len(normalized.longitude) == 2
    assert normalized.u.shape == (2, 2, 2)
    assert normalized.v.shape == (2, 2, 2)
    assert np.isclose(normalized.u[0, 0, 0], 1.5)
    assert np.isclose(normalized.v[0, 0, 0], 3.0)


def test_current_provider_fallback_to_hycom_records_provenance(monkeypatch):
    """
    CRITICAL CONTRACT TEST:
    When fallback is enabled and CMEMS is unconfigured, provider must record HYCOM in source
    and note fallback in provenance — never silently pretend to be CMEMS.
    """
    monkeypatch.setenv("CMEMS_USERNAME", "")
    monkeypatch.setenv("CMEMS_PASSWORD", "")

    cp = CurrentProvider()
    aoi = AOI(-90.5, 27.5, -89.5, 28.5)

    # Mock HYCOMReader.fetch_currents to simulate successful HYCOM download
    def mock_fetch(lon_min, lat_min, lon_max, lat_max, time_start, time_end, output_path):
        output_path.write_bytes(b"fake_hycom_netcdf_bytes")
        return output_path

    # Mock GenericForcingReader.read_netcdf_file
    def mock_read(file_path, variable_type, source, dataset_version, resolution, provenance=None):
        return NormalizedForcingData(
            variable_type=variable_type,
            timestamp=["2026-09-17T00:00:00Z"],
            latitude=[aoi.lat_min],
            longitude=[aoi.lon_min],
            u=np.array([[0.25]]),
            v=np.array([[0.10]]),
            source=source,
            dataset_version=dataset_version,
            resolution=resolution,
            provenance=provenance,
        )

    monkeypatch.setattr(cp.hycom_reader, "fetch_currents", mock_fetch)
    monkeypatch.setattr(cp.hycom_reader, "check_availability", lambda: (True, "ok"))
    monkeypatch.setattr(GenericForcingReader, "read_netcdf_file", mock_read)

    result = cp.get_currents(aoi, "2026-09-17T00:00:00Z", "2026-09-17T12:00:00Z", allow_fallback=True, use_cache=False)

    # Verification of strict non-silent substitution contract:
    assert result.source == "HYCOM", "Must identify real source as HYCOM, not CMEMS"
    assert "HYCOM" in result.dataset_version
    assert result.provenance is not None
    assert result.provenance.source_name == "HYCOM (Public THREDDS)"
    assert any("FALLBACK USED" in note for note in result.provenance.notes)


def test_ocean_forcing_status_endpoint():
    """Verify GET /api/v1/ocean/status reports live health of all providers."""
    import asyncio
    from app.api.v1.endpoints.ocean_forcing import get_providers_status

    status = asyncio.run(get_providers_status())
    assert "available" in status.era5_wind
    assert "available" in status.cmems_currents
    assert "available" in status.hycom_currents
    assert "available" in status.incois_currents
    assert "available" in status.cmems_waves

