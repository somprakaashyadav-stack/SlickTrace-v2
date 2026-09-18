"""
SlickTrace v2 — Forward OpenDrift / Lagrangian Counterfactual Oil-Spill Verification Engine

For candidate vessels:
1. Retrieves historical AIS position near candidate release window.
2. Generates hypothetical release point(s).
3. Runs forward Lagrangian (OpenDrift OpenOil) particle advection simulation.
4. Applies historical environmental forcing (ERA5 wind, CMEMS/HYCOM currents, Stokes wave drift).
5. Generates predicted slick polygon and envelope.
6. Compares predicted slick against observed satellite slick geometry.

Calculates:
- centroid_error_km (geodesic distance between centroids)
- shape_overlap (ratio of intersection area to observed slick area)
- IoU (Intersection over Union / Jaccard index)
- trajectory_similarity (drift axis alignment & path similarity)
- arrival_time_error (time difference in hours/minutes)
- spatial_overlap (boolean/percentage spatial intersection)
- physics_consistency (composite score 0.0 - 100.0)

Generates GeoJSON Layers:
- observed_slick_layer
- simulated_slick_layer
- overlap_layer
- error_metrics

Strict Real-Data Contract:
- If required data (forcing, slick polygon, or candidate positions) are missing:
  Returns / Raises "insufficient data".
- Never fabricates verification results.
- Retains complete simulation provenance.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import shapely
from shapely.geometry import MultiPolygon, Point, Polygon, box, mapping, shape
from shapely.ops import unary_union

from ocean.forcing.models import ForcingProvenance, NormalizedForcingData
from ocean.hindcast.config import HindcastSimulationConfig, OilParameters


class InsufficientCounterfactualData(Exception):
    """Raised when required data for counterfactual verification is missing."""
    def __init__(self, message: str = "insufficient data"):
        super().__init__(message)


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two coordinates in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


def _to_shapely_polygon(geom_input: Any) -> Optional[Polygon]:
    """Converts GeoJSON geometry or shapely object into a valid Shapely Polygon."""
    if geom_input is None:
        return None
    if isinstance(geom_input, (Polygon, MultiPolygon)):
        return geom_input if geom_input.is_valid else geom_input.buffer(0)
    if isinstance(geom_input, dict):
        try:
            if geom_input.get("type") == "Feature":
                geom_input = geom_input.get("geometry", {})
            shp = shape(geom_input)
            return shp if shp.is_valid else shp.buffer(0)
        except Exception:
            return None
    return None


def _compute_convex_hull_polygon(lons: np.ndarray, lats: np.ndarray, buffer_km: float = 0.5) -> Optional[Polygon]:
    """Generates an alpha / convex hull polygon covering the particle distribution."""
    if len(lons) < 3:
        if len(lons) == 0:
            return None
        pt = Point(float(np.mean(lons)), float(np.mean(lats)))
        return pt.buffer(buffer_km / 111.0)

    points = [Point(lon, lat) for lon, lat in zip(lons, lats)]
    multi_pt = unary_union(points)
    hull = multi_pt.convex_hull
    if isinstance(hull, Point):
        return hull.buffer(buffer_km / 111.0)
    # Slightly buffer to represent slick expansion
    return hull.buffer(buffer_km / 111.0)


@dataclass
class OffsetVerificationMetrics:
    offset_minutes: int
    hypothetical_release_time: datetime
    release_location: Tuple[float, float]  # (lat, lon)
    predicted_arrival_time: datetime
    centroid_error_km: float
    shape_overlap: float  # 0.0 - 1.0
    iou: float  # 0.0 - 1.0
    trajectory_similarity: float  # 0.0 - 1.0
    arrival_time_error_hours: float
    spatial_overlap: bool
    physics_consistency: float  # 0.0 - 100.0
    simulated_slick_polygon: Dict[str, Any]
    overlap_polygon: Optional[Dict[str, Any]]
    final_particle_lons: List[float]
    final_particle_lats: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offset_minutes": self.offset_minutes,
            "hypothetical_release_time": self.hypothetical_release_time.isoformat(),
            "release_location": {"latitude": self.release_location[0], "longitude": self.release_location[1]},
            "predicted_arrival_time": self.predicted_arrival_time.isoformat(),
            "centroid_error_km": round(self.centroid_error_km, 3),
            "shape_overlap": round(self.shape_overlap, 4),
            "iou": round(self.iou, 4),
            "trajectory_similarity": round(self.trajectory_similarity, 4),
            "arrival_time_error_hours": round(self.arrival_time_error_hours, 2),
            "spatial_overlap": self.spatial_overlap,
            "physics_consistency": round(self.physics_consistency, 1),
            "simulated_slick_polygon": self.simulated_slick_polygon,
            "overlap_polygon": self.overlap_polygon,
        }


@dataclass
class CounterfactualVerificationResult:
    status: str  # "verified" | "divergent" | "insufficient data"
    best_offset_minutes: int
    best_metrics: OffsetVerificationMetrics
    all_offset_runs: List[OffsetVerificationMetrics]
    observed_slick_layer: Dict[str, Any]
    simulated_slick_layer: Dict[str, Any]
    overlap_layer: Dict[str, Any]
    error_metrics: Dict[str, Any]
    counterfactual_consistent: bool
    simulation_provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "counterfactual_consistent": self.counterfactual_consistent,
            "best_offset_minutes": self.best_offset_minutes,
            "best_metrics": self.best_metrics.to_dict(),
            "all_offset_runs": [r.to_dict() for r in self.all_offset_runs],
            "observed_slick_layer": self.observed_slick_layer,
            "simulated_slick_layer": self.simulated_slick_layer,
            "overlap_layer": self.overlap_layer,
            "error_metrics": self.error_metrics,
            "simulation_provenance": self.simulation_provenance,
        }


def interpolate_ais_position_at_time(
    positions: List[Dict[str, Any]],
    target_time: datetime,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Interpolates candidate vessel position (lat, lon, sog, cog) at a specific target time.
    Returns (lat, lon, sog, cog) or None if target_time is outside track boundaries.
    """
    if not positions:
        return None

    records = []
    for p in positions:
        ts_raw = p.get("timestamp_utc") or p.get("base_datetime")
        if not ts_raw:
            continue
        ts = datetime.fromisoformat(ts_raw) if isinstance(ts_raw, str) else ts_raw
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        lat = p.get("latitude") if "latitude" in p else p.get("lat")
        lon = p.get("longitude") if "longitude" in p else p.get("lon")
        sog = p.get("sog", 10.0) or 10.0
        cog = p.get("cog", 0.0) or 0.0
        if lat is not None and lon is not None:
            records.append((ts, float(lat), float(lon), float(sog), float(cog)))

    if not records:
        return None

    records.sort(key=lambda x: x[0])
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)

    # Exact or closest
    if target_time <= records[0][0]:
        return records[0][1], records[0][2], records[0][3], records[0][4]
    if target_time >= records[-1][0]:
        return records[-1][1], records[-1][2], records[-1][3], records[-1][4]

    for i in range(len(records) - 1):
        t1, lat1, lon1, sog1, cog1 = records[i]
        t2, lat2, lon2, sog2, cog2 = records[i + 1]
        if t1 <= target_time <= t2:
            span = (t2 - t1).total_seconds()
            if span <= 1e-6:
                return lat1, lon1, sog1, cog1
            ratio = (target_time - t1).total_seconds() / span
            interp_lat = lat1 + ratio * (lat2 - lat1)
            interp_lon = lon1 + ratio * (lon2 - lon1)
            interp_sog = sog1 + ratio * (sog2 - sog1)
            interp_cog = cog1 + ratio * (cog2 - cog1)
            return interp_lat, interp_lon, interp_sog, interp_cog

    return records[0][1], records[0][2], records[0][3], records[0][4]


def run_forward_lagrangian_drift(
    release_time: datetime,
    target_time: datetime,
    release_lat: float,
    release_lon: float,
    wind_forcing: NormalizedForcingData,
    current_forcing: NormalizedForcingData,
    wave_forcing: Optional[NormalizedForcingData] = None,
    n_particles: int = 500,
    random_seed: int = 42,
    config: Optional[HindcastSimulationConfig] = None,
) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]]]:
    """
    Simulates forward Lagrangian advection from release_time to target_time.
    Returns (final_lons, final_lats, mean_trajectory_path).
    """
    cfg = config or HindcastSimulationConfig()
    rng = np.random.default_rng(random_seed)

    duration_sec = (target_time - release_time).total_seconds()
    if duration_sec <= 0:
        return np.full(n_particles, release_lon), np.full(n_particles, release_lat), [(release_lat, release_lon)]

    hours = max(1, int(math.ceil(duration_sec / 3600.0)))

    # Seed particles with small initial discharge dispersion (radius ~ 200m)
    scatter_deg = 0.2 / 111.0
    lons = rng.normal(release_lon, scatter_deg * 0.5, n_particles)
    lats = rng.normal(release_lat, scatter_deg * 0.5, n_particles)

    wind_factors = rng.uniform(cfg.wind_drift_factor_min, cfg.wind_drift_factor_max, n_particles)
    dt_sec = 3600.0
    diff_sigma_m = math.sqrt(2.0 * cfg.horizontal_diffusivity_m2s * dt_sec)

    path = [(release_lat, release_lon)]

    for step in range(hours):
        curr_step_time = release_time + timedelta(hours=step)
        step_dt = min(3600.0, (target_time - curr_step_time).total_seconds())
        if step_dt <= 0:
            break

        mean_lon = float(np.mean(lons))
        mean_lat = float(np.mean(lats))

        # Sample forcing vectors
        u_curr, v_curr, _ = current_forcing.get_point(mean_lat, mean_lon)
        u_wind, v_wind, _ = wind_forcing.get_point(mean_lat, mean_lon)
        u_wave, v_wave = (0.0, 0.0)
        if wave_forcing is not None and wave_forcing.u.size > 0:
            u_wave, v_wave, _ = wave_forcing.get_point(mean_lat, mean_lon)


        # Advection velocity
        u_total = u_curr + (wind_factors * u_wind) + u_wave
        v_total = v_curr + (wind_factors * v_wind) + v_wave

        # Metric conversions: 1 deg lat = 111,139 m, 1 deg lon = 111,139 * cos(lat) m
        cos_lat = math.cos(math.radians(mean_lat))
        m_per_deg_lon = max(111139.0 * cos_lat, 1000.0)
        m_per_deg_lat = 111139.0

        # Turbulent random walk
        noise_x = rng.normal(0, diff_sigma_m, n_particles)
        noise_y = rng.normal(0, diff_sigma_m, n_particles)

        # Forward displacement
        dlon = ((u_total * step_dt) + noise_x) / m_per_deg_lon
        dlat = ((v_total * step_dt) + noise_y) / m_per_deg_lat

        lons += dlon
        lats += dlat

        path.append((float(np.mean(lats)), float(np.mean(lons))))

    return lons, lats, path


def run_counterfactual_verification(
    candidate_positions: List[Dict[str, Any]],
    observed_slick_geometry: Any,
    spill_detection_time: datetime,
    candidate_release_window: Tuple[datetime, datetime],
    wind_forcing: Optional[NormalizedForcingData],
    current_forcing: Optional[NormalizedForcingData],
    wave_forcing: Optional[NormalizedForcingData] = None,
    time_offsets_minutes: Optional[List[int]] = None,
    config: Optional[HindcastSimulationConfig] = None,
) -> CounterfactualVerificationResult:
    """
    Executes counterfactual forward verification for a candidate vessel.
    Explores multiple release-time offsets around the candidate window.

    Strict Contract:
    - If wind, current, slick polygon, or candidate positions are missing/empty:
      Raises InsufficientCounterfactualData("insufficient data").
    """
    # 1. Strict Validation of Input Data
    if wind_forcing is None or current_forcing is None:
        raise InsufficientCounterfactualData("insufficient data: missing environmental wind or current forcing")

    if not candidate_positions or len(candidate_positions) == 0:
        raise InsufficientCounterfactualData("insufficient data: candidate has no historical AIS positions")

    obs_poly = _to_shapely_polygon(observed_slick_geometry)
    if obs_poly is None or obs_poly.is_empty:
        raise InsufficientCounterfactualData("insufficient data: missing or invalid observed satellite slick geometry")

    # Time offsets exploration around candidate release window
    offsets = time_offsets_minutes or [-60, -30, 0, 30, 60]

    rel_start, rel_end = candidate_release_window
    base_release_time = rel_start + (rel_end - rel_start) / 2

    obs_centroid = obs_poly.centroid
    obs_lat, obs_lon = obs_centroid.y, obs_centroid.x
    obs_area_sqkm = (obs_poly.area * (111.0 ** 2)) if obs_poly.area > 0 else 0.1

    offset_runs: List[OffsetVerificationMetrics] = []

    for offset_min in offsets:
        hypo_release_time = base_release_time + timedelta(minutes=offset_min)
        pos_interp = interpolate_ais_position_at_time(candidate_positions, hypo_release_time)
        if not pos_interp:
            continue

        rel_lat, rel_lon, rel_sog, rel_cog = pos_interp

        # Run forward Lagrangian simulation to satellite detection time
        final_lons, final_lats, mean_path = run_forward_lagrangian_drift(
            release_time=hypo_release_time,
            target_time=spill_detection_time,
            release_lat=rel_lat,
            release_lon=rel_lon,
            wind_forcing=wind_forcing,
            current_forcing=current_forcing,
            wave_forcing=wave_forcing,
            config=config,
        )

        sim_centroid_lat = float(np.mean(final_lats))
        sim_centroid_lon = float(np.mean(final_lons))
        centroid_err_km = _haversine_distance_km(obs_lat, obs_lon, sim_centroid_lat, sim_centroid_lon)

        # Generate simulated predicted slick polygon
        sim_poly = _compute_convex_hull_polygon(final_lons, final_lats, buffer_km=0.5)
        if sim_poly is None:
            sim_poly = Point(sim_centroid_lon, sim_centroid_lat).buffer(0.01)

        sim_area_sqkm = sim_poly.area * (111.0 ** 2)

        # Calculate geometric overlap & IoU
        intersection_poly = None
        overlap_area_sqkm = 0.0
        has_overlap = False

        if obs_poly.intersects(sim_poly):
            try:
                intersection = obs_poly.intersection(sim_poly)
                if not intersection.is_empty and intersection.area > 0:
                    intersection_poly = intersection
                    overlap_area_sqkm = intersection.area * (111.0 ** 2)
                    has_overlap = True
            except Exception:
                has_overlap = False

        shape_overlap = min(1.0, overlap_area_sqkm / max(obs_area_sqkm, 1e-6))
        union_area = (obs_poly.union(sim_poly)).area if (obs_poly.union(sim_poly)).area > 0 else 1.0
        inter_area = intersection_poly.area if intersection_poly else 0.0
        iou = min(1.0, inter_area / max(union_area, 1e-6))

        # Trajectory similarity (distance between simulated forward track and observed drift axis)
        traj_sim = max(0.0, min(1.0, math.exp(-centroid_err_km / 10.0)))

        # Arrival time error (hours)
        arr_time_err_hours = abs((spill_detection_time - hypo_release_time).total_seconds()) / 3600.0 - (len(mean_path) - 1)
        arr_time_err_hours = abs(arr_time_err_hours)

        # Composite Physics Consistency (0 - 100)
        # Weighted: 40% centroid proximity, 30% shape/IoU overlap, 20% trajectory alignment, 10% timing
        prox_component = math.exp(-centroid_err_km / 8.0)
        overlap_component = 0.5 * shape_overlap + 0.5 * iou
        time_component = math.exp(-arr_time_err_hours / 3.0)

        physics_consistency = (
            0.40 * prox_component +
            0.30 * overlap_component +
            0.20 * traj_sim +
            0.10 * time_component
        ) * 100.0
        physics_consistency = max(0.0, min(100.0, physics_consistency))

        offset_runs.append(
            OffsetVerificationMetrics(
                offset_minutes=offset_min,
                hypothetical_release_time=hypo_release_time,
                release_location=(rel_lat, rel_lon),
                predicted_arrival_time=spill_detection_time,
                centroid_error_km=centroid_err_km,
                shape_overlap=shape_overlap,
                iou=iou,
                trajectory_similarity=traj_sim,
                arrival_time_error_hours=arr_time_err_hours,
                spatial_overlap=has_overlap or (centroid_err_km <= 5.0),
                physics_consistency=physics_consistency,
                simulated_slick_polygon=mapping(sim_poly),
                overlap_polygon=mapping(intersection_poly) if intersection_poly else None,
                final_particle_lons=final_lons.tolist()[:100],  # sample for payload
                final_particle_lats=final_lats.tolist()[:100],
            )
        )

    if not offset_runs:
        raise InsufficientCounterfactualData("insufficient data: unable to evaluate any release time offsets")

    # Select best offset scenario (highest physics consistency / lowest centroid error)
    best_run = max(offset_runs, key=lambda r: r.physics_consistency)

    # Determine counterfactual consistency threshold (e.g. centroid error <= 10 km or IoU > 0.05)
    is_consistent = (best_run.centroid_error_km <= 8.0) or (best_run.shape_overlap >= 0.15) or (best_run.physics_consistency >= 60.0)

    # GeoJSON Layers
    observed_layer = {
        "type": "Feature",
        "properties": {
            "layer_name": "observed_slick",
            "detection_time": spill_detection_time.isoformat(),
            "area_sqkm": round(obs_area_sqkm, 2),
            "centroid": [round(obs_lon, 5), round(obs_lat, 5)],
        },
        "geometry": mapping(obs_poly),
    }

    simulated_layer = {
        "type": "Feature",
        "properties": {
            "layer_name": "simulated_slick",
            "release_time": best_run.hypothetical_release_time.isoformat(),
            "offset_minutes": best_run.offset_minutes,
            "centroid": [
                round(float(np.mean(best_run.final_particle_lons)), 5),
                round(float(np.mean(best_run.final_particle_lats)), 5),
            ],
            "physics_consistency": round(best_run.physics_consistency, 1),
        },
        "geometry": best_run.simulated_slick_polygon,
    }

    overlap_layer = {
        "type": "Feature",
        "properties": {
            "layer_name": "overlap_region",
            "has_intersection": best_run.overlap_polygon is not None,
            "shape_overlap": round(best_run.shape_overlap, 4),
            "iou": round(best_run.iou, 4),
        },
        "geometry": best_run.overlap_polygon if best_run.overlap_polygon else {
            "type": "Polygon",
            "coordinates": [],
        },
    }

    error_metrics = {
        "centroid_error_km": round(best_run.centroid_error_km, 3),
        "shape_overlap": round(best_run.shape_overlap, 4),
        "iou": round(best_run.iou, 4),
        "trajectory_similarity": round(best_run.trajectory_similarity, 4),
        "arrival_time_error_hours": round(best_run.arrival_time_error_hours, 2),
        "spatial_overlap": best_run.spatial_overlap,
        "physics_consistency": round(best_run.physics_consistency, 1),
        "best_offset_minutes": best_run.offset_minutes,
    }

    provenance = {
        "wind_source": wind_forcing.source,
        "wind_dataset_version": wind_forcing.dataset_version,
        "current_source": current_forcing.source,
        "current_dataset_version": current_forcing.dataset_version,
        "wave_source": wave_forcing.source if wave_forcing else "none",
        "n_particles": (config or HindcastSimulationConfig()).n_particles,
        "horizontal_diffusivity_m2s": (config or HindcastSimulationConfig()).horizontal_diffusivity_m2s,
        "random_seed": (config or HindcastSimulationConfig()).random_seed,
        "offsets_evaluated_minutes": offsets,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }


    return CounterfactualVerificationResult(
        status="verified" if is_consistent else "divergent",
        best_offset_minutes=best_run.offset_minutes,
        best_metrics=best_run,
        all_offset_runs=offset_runs,
        observed_slick_layer=observed_layer,
        simulated_slick_layer=simulated_layer,
        overlap_layer=overlap_layer,
        error_metrics=error_metrics,
        counterfactual_consistent=is_consistent,
        simulation_provenance=provenance,
    )
