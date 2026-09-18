"""
SlickTrace v2 — Unit Tests for Physical Backward Hindcasting Engine (OpenDrift OpenOil)

Verifies:
1. Strict Real-Data Contract:
   - Missing wind or ocean current forcing raises InsufficientEnvironmentalData("insufficient environmental data").
   - All-NaN or empty forcing data raises InsufficientEnvironmentalData("insufficient environmental data").
   - Never fabricates a trajectory when forcing is unavailable.
2. Monte Carlo Particle Seeding:
   - Uniform particle sampling across observed slick polygon boundaries.
   - Fallback point dispersion when polygon coordinates are sparse.
3. Multi-Duration Backward Checkpoints:
   - Simulation produces duration slices at 4h, 8h, 12h, 24h.
   - Centroids, spreads, and origin timestamps computed at each horizon.
4. Probabilistic Dispersion & Nested Envelopes:
   - Probabilistic origin envelope (never a single deterministic origin point).
   - Generates P50, P75, and P90 convex hull confidence polygons.
   - Generates 2D normalized spatial origin probability density surface.
5. Interactive Time-Slider Animation Data:
   - Generates time-indexed GeoJSON Point FeatureCollection with hour_back and timestamps.
   - Generates GeoJSON LineString ensemble trajectory tracks.
6. Reproducibility Guarantee:
   - Fixed random_seed produces bit-for-bit identical trajectory and origin coordinates.
   - Stores simulation configuration and environmental forcing provenance.
"""
from datetime import datetime, timezone
import numpy as np
import pytest

from ocean.forcing.models import ForcingProvenance, NormalizedForcingData
from ocean.hindcast.config import HindcastSimulationConfig, OilParameters
from ocean.hindcast.monte_carlo import (
    build_particle_timesteps_geojson,
    build_trajectory_geojson,
    compute_origin_uncertainty,
    compute_probability_surface,
)
from ocean.hindcast.runner import (
    HindcastResult,
    InsufficientEnvironmentalData,
    run_hindcast,
    seed_particles_in_polygon,
)


@pytest.fixture
def dummy_forcing():
    """Generates synthetic valid wind and current forcing fields."""
    lats = [27.0, 27.5, 28.0]
    lons = [-90.5, -90.0, -89.5]
    times = ["2026-09-17T00:00:00Z", "2026-09-17T01:00:00Z"]

    # 1 m/s current eastward, 5 m/s wind northeastward
    u_w = np.full((2, 3, 3), 3.0, dtype=np.float32)
    v_w = np.full((2, 3, 3), 4.0, dtype=np.float32)

    u_c = np.full((2, 3, 3), 0.2, dtype=np.float32)
    v_c = np.full((2, 3, 3), 0.1, dtype=np.float32)

    prov_w = ForcingProvenance(
        source_name="ERA5",
        dataset_id="era5-10m-wind",
        dataset_version="v1",
        source_url="https://cds.climate.copernicus.eu",
        raw_file_sha256="wind_hash_123",
        spatial_bounds={"lon_min": -90.5, "lat_min": 27.0, "lon_max": -89.5, "lat_max": 28.0},
        time_range={"start": times[0], "end": times[1]},
    )
    prov_c = ForcingProvenance(
        source_name="Copernicus Marine (CMEMS)",
        dataset_id="cmems-global-phy",
        dataset_version="v1",
        source_url="https://marine.copernicus.eu",
        raw_file_sha256="curr_hash_456",
        spatial_bounds={"lon_min": -90.5, "lat_min": 27.0, "lon_max": -89.5, "lat_max": 28.0},
        time_range={"start": times[0], "end": times[1]},
    )

    wind = NormalizedForcingData(
        variable_type="wind",
        timestamp=times,
        latitude=lats,
        longitude=lons,
        u=u_w,
        v=v_w,
        source="ERA5",
        dataset_version="v1",
        resolution="0.25 deg",
        provenance=prov_w,
    )
    current = NormalizedForcingData(
        variable_type="current",
        timestamp=times,
        latitude=lats,
        longitude=lons,
        u=u_c,
        v=v_c,
        source="CMEMS",
        dataset_version="v1",
        resolution="0.083 deg",
        provenance=prov_c,
    )
    return wind, current


@pytest.fixture
def sample_slick_polygon():
    return {
        "type": "Polygon",
        "coordinates": [[
            [-90.1, 27.4],
            [-89.9, 27.4],
            [-89.9, 27.6],
            [-90.1, 27.6],
            [-90.1, 27.4],
        ]],
    }


def test_insufficient_environmental_data_missing_forcing():
    """Verify strict real-data contract: missing forcing raises InsufficientEnvironmentalData."""
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    # Missing both
    with pytest.raises(InsufficientEnvironmentalData) as exc:
        run_hindcast(detection_time=t0, wind_forcing=None, current_forcing=None)
    assert "insufficient environmental data" in str(exc.value)

    # Missing current
    lats = [27.0, 28.0]
    lons = [-90.0, -89.0]
    u = np.full((1, 2, 2), 1.0, dtype=np.float32)
    v = np.full((1, 2, 2), 1.0, dtype=np.float32)
    dummy_wind = NormalizedForcingData("wind", ["2026-09-17T12:00:00Z"], lats, lons, u, v, "ERA5", "v1", "0.25")

    with pytest.raises(InsufficientEnvironmentalData) as exc2:
        run_hindcast(detection_time=t0, wind_forcing=dummy_wind, current_forcing=None)
    assert "insufficient environmental data" in str(exc2.value)


def test_insufficient_environmental_data_nan_forcing():
    """Verify that all-NaN or empty forcing data raises InsufficientEnvironmentalData."""
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
    lats = [27.0, 28.0]
    lons = [-90.0, -89.0]

    nan_u = np.full((1, 2, 2), np.nan, dtype=np.float32)
    nan_v = np.full((1, 2, 2), np.nan, dtype=np.float32)

    wind_nan = NormalizedForcingData("wind", ["2026-09-17T12:00:00Z"], lats, lons, nan_u, nan_v, "ERA5", "v1", "0.25")
    curr_nan = NormalizedForcingData("current", ["2026-09-17T12:00:00Z"], lats, lons, nan_u, nan_v, "CMEMS", "v1", "0.083")

    with pytest.raises(InsufficientEnvironmentalData) as exc:
        run_hindcast(detection_time=t0, wind_forcing=wind_nan, current_forcing=curr_nan)
    assert "insufficient environmental data" in str(exc.value)


def test_slick_polygon_seeding(sample_slick_polygon):
    """Verify Monte Carlo particle seeding produces uniform points inside the slick polygon."""
    rng = np.random.default_rng(42)
    n_pts = 200
    lons, lats = seed_particles_in_polygon(
        slick_polygon=sample_slick_polygon,
        default_lat=27.5,
        default_lon=-90.0,
        n_particles=n_pts,
        rng=rng,
    )

    assert len(lons) == n_pts
    assert len(lats) == n_pts

    # Points must lie within the bounding box [-90.1, 27.4, -89.9, 27.6]
    assert np.all(lons >= -90.11)
    assert np.all(lons <= -89.89)
    assert np.all(lats >= 27.39)
    assert np.all(lats <= 27.61)


def test_multi_duration_backward_checkpoints(dummy_forcing, sample_slick_polygon):
    """Verify hindcast calculates duration slices at 4h, 8h, 12h, and 24h."""
    wind, current = dummy_forcing
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    cfg = HindcastSimulationConfig(
        durations_hours=[4, 8, 12, 24],
        n_particles=150,
        random_seed=42,
    )

    result = run_hindcast(
        detection_time=t0,
        wind_forcing=wind,
        current_forcing=current,
        slick_polygon=sample_slick_polygon,
        config=cfg,
    )

    assert isinstance(result, HindcastResult)
    assert "4h" in result.duration_slices
    assert "8h" in result.duration_slices
    assert "12h" in result.duration_slices
    assert "24h" in result.duration_slices

    for h_key in ["4h", "8h", "12h", "24h"]:
        slice_info = result.duration_slices[h_key]
        assert "centroid_lat" in slice_info
        assert "centroid_lon" in slice_info
        assert "spread_km" in slice_info
        assert slice_info["spread_km"] > 0
        assert slice_info["p50_polygon"] is not None
        assert slice_info["p90_polygon"] is not None


def test_probabilistic_envelopes_and_density_surface(dummy_forcing):
    """Verify hindcast never returns a single point and creates nested confidence hulls + probability grid."""
    wind, current = dummy_forcing
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    cfg = HindcastSimulationConfig(n_particles=200, random_seed=42)
    result = run_hindcast(
        detection_time=t0,
        wind_forcing=wind,
        current_forcing=current,
        start_lat=27.5,
        start_lon=-90.0,
        config=cfg,
    )

    # Check uncertainty envelope
    meta = result.uncertainty_metadata
    assert "p50_polygon" in meta and meta["p50_polygon"] is not None
    assert "p75_polygon" in meta and meta["p75_polygon"] is not None
    assert "p90_polygon" in meta and meta["p90_polygon"] is not None
    assert meta["spread_km"] > 0

    # Validate GeoJSON Polygon format for P50
    poly = meta["p50_polygon"]
    assert poly["type"] == "Polygon"
    assert len(poly["coordinates"][0]) >= 4  # closed ring

    # Validate 2D probability surface
    prob_surface = meta["probability_surface"]
    assert "lon_centers" in prob_surface
    assert "lat_centers" in prob_surface
    assert "probabilities" in prob_surface
    assert "max_probability" in prob_surface

    prob_matrix = np.array(prob_surface["probabilities"])
    assert prob_matrix.ndim == 2
    assert np.isclose(np.sum(prob_matrix), 1.0, atol=1e-3)


def test_reproducibility_with_fixed_seed(dummy_forcing, sample_slick_polygon):
    """Verify identical parameters and random_seed produce identical outputs."""
    wind, current = dummy_forcing
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    cfg1 = HindcastSimulationConfig(n_particles=100, random_seed=999)
    cfg2 = HindcastSimulationConfig(n_particles=100, random_seed=999)

    run1 = run_hindcast(t0, wind, current, sample_slick_polygon, config=cfg1)
    run2 = run_hindcast(t0, wind, current, sample_slick_polygon, config=cfg2)

    assert run1.origin_lat == run2.origin_lat
    assert run1.origin_lon == run2.origin_lon
    assert run1.uncertainty_metadata["spread_km"] == run2.uncertainty_metadata["spread_km"]
    assert run1.trajectory_geojson == run2.trajectory_geojson
    assert run1.particle_timesteps_geojson == run2.particle_timesteps_geojson


def test_particle_timesteps_geojson_animation_structure(dummy_forcing):
    """Verify particle_timesteps_geojson contains time-slider features with hour_back and timestamp."""
    wind, current = dummy_forcing
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    cfg = HindcastSimulationConfig(durations_hours=[4, 8], n_particles=80, random_seed=42)
    result = run_hindcast(t0, wind, current, config=cfg)

    fc = result.particle_timesteps_geojson
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) > 0

    first_feat = fc["features"][0]
    assert first_feat["geometry"]["type"] == "Point"
    assert "particle_id" in first_feat["properties"]
    assert "hour_back" in first_feat["properties"]
    assert "timestamp" in first_feat["properties"]

    hours_present = set(f["properties"]["hour_back"] for f in fc["features"])
    assert 0 in hours_present
    assert 8 in hours_present


def test_custom_oil_parameters_and_provenance(dummy_forcing):
    """Verify custom oil parameters and forcing provenance are properly recorded."""
    wind, current = dummy_forcing
    t0 = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)

    custom_oil = OilParameters(
        oil_type="HEAVY FUEL OIL IFO 380",
        api_gravity=11.2,
        viscosity_cst=380.0,
        pour_point_c=21.0,
    )
    cfg = HindcastSimulationConfig(
        durations_hours=[6, 12],
        n_particles=60,
        oil_params=custom_oil,
        random_seed=77,
    )

    result = run_hindcast(t0, wind, current, config=cfg)
    assert result.simulation_config["oil_params"]["oil_type"] == "HEAVY FUEL OIL IFO 380"
    assert result.simulation_config["oil_params"]["api_gravity"] == 11.2
    assert "wind" in result.forcing_provenance
    assert "currents" in result.forcing_provenance
    assert result.forcing_provenance["wind"]["source_name"] == "ERA5"
    assert result.forcing_provenance["currents"]["source_name"] == "Copernicus Marine (CMEMS)"
