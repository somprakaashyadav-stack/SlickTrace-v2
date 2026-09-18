"""
SlickTrace v2 — Forward Counterfactual Oil-Spill Verification Test Suite
"""
import pytest
from datetime import datetime, timedelta, timezone
import numpy as np
from shapely.geometry import Polygon, mapping

from ocean.forcing.models import ForcingProvenance, NormalizedForcingData
from ocean.hindcast.counterfactual import (
    run_counterfactual_verification,
    run_forward_lagrangian_drift,
    interpolate_ais_position_at_time,
    InsufficientCounterfactualData,
)


def _create_mock_forcing(source_name: str, u_val: float, v_val: float) -> NormalizedForcingData:
    base = datetime(2026, 9, 16, 0, 0, 0, tzinfo=timezone.utc)
    times = [(base + timedelta(hours=i)).isoformat() for i in range(48)]
    lats = [27.0, 27.5, 28.0, 28.5]
    lons = [-91.0, -90.5, -90.0, -89.5]

    u = np.full((len(times), len(lats), len(lons)), u_val)
    v = np.full((len(times), len(lats), len(lons)), v_val)

    prov = ForcingProvenance(
        source_name=source_name,
        dataset_id="test_ds",
        dataset_version="v1.0",
        source_url="https://example.com/data",
        raw_file_sha256="test_hash",
        spatial_bounds={"lon_min": -91.0, "lat_min": 27.0, "lon_max": -89.5, "lat_max": 28.5},
        time_range={"start": times[0], "end": times[-1]},
    )

    return NormalizedForcingData(
        variable_type="wind" if "wind" in source_name.lower() else "current",
        timestamp=times,
        latitude=lats,
        longitude=lons,
        u=u,
        v=v,
        source=source_name,
        dataset_version="v1.0",
        resolution="0.5 deg, 1h",
        provenance=prov,
    )



def test_interpolate_ais_position():
    base = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp_utc": (base).isoformat(), "latitude": 27.0, "longitude": -90.0, "sog": 10.0, "cog": 45.0},
        {"timestamp_utc": (base + timedelta(hours=2)).isoformat(), "latitude": 28.0, "longitude": -89.0, "sog": 12.0, "cog": 45.0},
    ]

    target = base + timedelta(hours=1)
    res = interpolate_ais_position_at_time(positions, target)
    assert res is not None
    lat, lon, sog, cog = res
    assert lat == 27.5
    assert lon == -89.5
    assert sog == 11.0


def test_counterfactual_verification_full_pipeline():
    detection_time = datetime(2026, 9, 16, 18, 0, 0, tzinfo=timezone.utc)
    release_window = (detection_time - timedelta(hours=6), detection_time - timedelta(hours=4))

    # Observed slick at detection time
    obs_poly = Polygon([[-89.85, 27.65], [-89.75, 27.65], [-89.75, 27.75], [-89.85, 27.75]])

    # Candidate vessel track passing near origin ~5 hours before detection
    # With eastward current (u=0.5 m/s, ~1.8 km/h -> in 5h moves ~9 km east)
    vessel_positions = [
        {"timestamp_utc": (detection_time - timedelta(hours=6)).isoformat(), "latitude": 27.70, "longitude": -89.95, "sog": 10.0, "cog": 90.0},
        {"timestamp_utc": (detection_time - timedelta(hours=5)).isoformat(), "latitude": 27.70, "longitude": -89.90, "sog": 10.0, "cog": 90.0},
        {"timestamp_utc": (detection_time - timedelta(hours=4)).isoformat(), "latitude": 27.70, "longitude": -89.85, "sog": 10.0, "cog": 90.0},
    ]

    wind = _create_mock_forcing("ERA5_Wind", u_val=2.0, v_val=0.0)  # Gentle eastward wind
    current = _create_mock_forcing("CMEMS_Current", u_val=0.2, v_val=0.0)  # Eastward current

    result = run_counterfactual_verification(
        candidate_positions=vessel_positions,
        observed_slick_geometry=mapping(obs_poly),
        spill_detection_time=detection_time,
        candidate_release_window=release_window,
        wind_forcing=wind,
        current_forcing=current,
        time_offsets_minutes=[-30, 0, 30],
    )

    # Status and metrics checks
    assert result.status in ("verified", "divergent")
    assert result.best_metrics.centroid_error_km >= 0.0
    assert 0.0 <= result.best_metrics.shape_overlap <= 1.0
    assert 0.0 <= result.best_metrics.iou <= 1.0
    assert 0.0 <= result.best_metrics.trajectory_similarity <= 1.0
    assert result.best_metrics.arrival_time_error_hours >= 0.0
    assert 0.0 <= result.best_metrics.physics_consistency <= 100.0

    # GeoJSON layer generation checks
    assert result.observed_slick_layer["type"] == "Feature"
    assert result.observed_slick_layer["properties"]["layer_name"] == "observed_slick"

    assert result.simulated_slick_layer["type"] == "Feature"
    assert result.simulated_slick_layer["properties"]["layer_name"] == "simulated_slick"

    assert result.overlap_layer["type"] == "Feature"
    assert result.overlap_layer["properties"]["layer_name"] == "overlap_region"

    # Multi-offset exploration check
    assert len(result.all_offset_runs) == 3

    # Provenance check
    prov = result.simulation_provenance
    assert prov["wind_source"] == "ERA5_Wind"
    assert prov["current_source"] == "CMEMS_Current"
    assert prov["offsets_evaluated_minutes"] == [-30, 0, 30]


def test_counterfactual_insufficient_data_handling():
    detection_time = datetime(2026, 9, 16, 18, 0, 0, tzinfo=timezone.utc)
    release_window = (detection_time - timedelta(hours=6), detection_time - timedelta(hours=4))
    obs_poly = Polygon([[-89.85, 27.65], [-89.75, 27.65], [-89.75, 27.75], [-89.85, 27.75]])

    # Missing forcing: should raise InsufficientCounterfactualData without fabricating
    with pytest.raises(InsufficientCounterfactualData) as exc:
        run_counterfactual_verification(
            candidate_positions=[{"timestamp_utc": detection_time.isoformat(), "latitude": 27.7, "longitude": -89.9}],
            observed_slick_geometry=mapping(obs_poly),
            spill_detection_time=detection_time,
            candidate_release_window=release_window,
            wind_forcing=None,  # Missing
            current_forcing=None,  # Missing
        )
    assert "insufficient data" in str(exc.value).lower()

    # Missing AIS positions: should raise InsufficientCounterfactualData
    wind = _create_mock_forcing("ERA5_Wind", u_val=2.0, v_val=0.0)
    current = _create_mock_forcing("CMEMS_Current", u_val=0.2, v_val=0.0)
    with pytest.raises(InsufficientCounterfactualData) as exc:
        run_counterfactual_verification(
            candidate_positions=[],  # Empty
            observed_slick_geometry=mapping(obs_poly),
            spill_detection_time=detection_time,
            candidate_release_window=release_window,
            wind_forcing=wind,
            current_forcing=current,
        )
    assert "insufficient data" in str(exc.value).lower()
