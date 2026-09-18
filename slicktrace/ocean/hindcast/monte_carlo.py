"""
SlickTrace v2 — Monte Carlo Ensemble Analysis & Uncertainty Engine

Computes:
- Origin probability density surface
- Nested confidence origin polygons (50%, 75%, 90%)
- Time-stepped particle point collections for interactive backward animation
- Ensemble trajectory GeoJSON LineStrings
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


def _percentile_polygon(lons: np.ndarray, lats: np.ndarray, percentile: int) -> Optional[Dict[str, Any]]:
    """
    Build a convex hull polygon enclosing `percentile`% of particles
    closest to the centroid. Returns GeoJSON Polygon coordinates or None.
    """
    if len(lons) < 4:
        return None

    centroid_lon = float(np.median(lons))
    centroid_lat = float(np.median(lats))

    # Geodesic metric distance approximation in km
    lat_rad = math.radians(centroid_lat)
    m_per_deg_lat = 111.13
    m_per_deg_lon = 111.41 * math.cos(lat_rad)

    dists = np.sqrt(
        ((lons - centroid_lon) * m_per_deg_lon) ** 2 +
        ((lats - centroid_lat) * m_per_deg_lat) ** 2
    )

    threshold = float(np.percentile(dists, percentile))
    mask = dists <= threshold
    pts = np.column_stack([lons[mask], lats[mask]])

    if pts.shape[0] < 4:
        return None

    try:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(pts)
        hull_pts = pts[hull.vertices].tolist()
        hull_pts.append(hull_pts[0])  # close ring
        return {
            "type": "Polygon",
            "coordinates": [hull_pts],
        }
    except Exception:
        # Fallback bounding box
        min_x, max_x = float(np.min(pts[:, 0])), float(np.max(pts[:, 0]))
        min_y, max_y = float(np.min(pts[:, 1])), float(np.max(pts[:, 1]))
        return {
            "type": "Polygon",
            "coordinates": [[[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y], [min_x, min_y]]],
        }


def compute_origin_uncertainty(
    final_lons: np.ndarray,
    final_lats: np.ndarray,
) -> Dict[str, Any]:
    """
    Computes probabilistic origin envelope from particle ensemble coordinates
    at a specific backward time horizon.

    Returns:
    - centroid_lat, centroid_lon
    - p50_polygon (50% confidence boundary)
    - p75_polygon (75% confidence boundary)
    - p90_polygon (90% confidence boundary)
    - spread_km (90th percentile dispersion spread)
    - particle_count
    """
    valid = ~(np.isnan(final_lons) | np.isnan(final_lats))
    if not valid.any():
        return {
            "centroid_lat": 0.0,
            "centroid_lon": 0.0,
            "p50_polygon": None,
            "p75_polygon": None,
            "p90_polygon": None,
            "spread_km": 0.0,
            "particle_count": 0,
        }

    vlons = np.array(final_lons[valid], dtype=np.float64)
    vlats = np.array(final_lats[valid], dtype=np.float64)

    centroid_lon = float(np.median(vlons))
    centroid_lat = float(np.median(vlats))

    p50_poly = _percentile_polygon(vlons, vlats, percentile=50)
    p75_poly = _percentile_polygon(vlons, vlats, percentile=75)
    p90_poly = _percentile_polygon(vlons, vlats, percentile=90)

    # Approximate 90th percentile dispersion spread in km
    lat_rad = math.radians(centroid_lat)
    m_per_deg_lat = 111.13
    m_per_deg_lon = 111.41 * math.cos(lat_rad)
    lat_spread = (np.percentile(vlats, 95) - np.percentile(vlats, 5)) * m_per_deg_lat
    lon_spread = (np.percentile(vlons, 95) - np.percentile(vlons, 5)) * m_per_deg_lon
    spread_km = float(math.sqrt(lat_spread ** 2 + lon_spread ** 2))

    return {
        "centroid_lat": round(centroid_lat, 6),
        "centroid_lon": round(centroid_lon, 6),
        "p50_polygon": p50_poly,
        "p75_polygon": p75_poly,
        "p90_polygon": p90_poly,
        "spread_km": round(spread_km, 2),
        "particle_count": int(valid.sum()),
    }


def compute_probability_surface(
    lons: np.ndarray,
    lats: np.ndarray,
    n_bins: int = 40,
) -> Dict[str, Any]:
    """
    Computes a 2D spatial origin probability surface via binned spatial density.
    Returns grid coordinates, bounding box, and normalized probabilities (sum = 1.0).
    """
    valid = ~(np.isnan(lons) | np.isnan(lats))
    if not valid.any():
        return {"grid": [], "bbox": [0, 0, 0, 0], "max_probability": 0.0}

    vlons = lons[valid]
    vlats = lats[valid]

    min_lon, max_lon = float(np.min(vlons)), float(np.max(vlons))
    min_lat, max_lat = float(np.min(vlats)), float(np.max(vlats))

    # Add 10% padding
    pad_lon = max(0.01, (max_lon - min_lon) * 0.1)
    pad_lat = max(0.01, (max_lat - min_lat) * 0.1)

    lon_bins = np.linspace(min_lon - pad_lon, max_lon + pad_lon, n_bins)
    lat_bins = np.linspace(min_lat - pad_lat, max_lat + pad_lat, n_bins)

    H, _, _ = np.histogram2d(vlons, vlats, bins=[lon_bins, lat_bins])
    total = np.sum(H)
    prob_grid = (H / total if total > 0 else H).T  # shape: (n_lat_bins-1, n_lon_bins-1)

    return {
        "lon_centers": [round(float(x), 5) for x in (lon_bins[:-1] + lon_bins[1:]) / 2],
        "lat_centers": [round(float(y), 5) for y in (lat_bins[:-1] + lat_bins[1:]) / 2],
        "probabilities": [[round(float(v), 5) for v in row] for row in prob_grid],
        "bbox": [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)],
        "max_probability": round(float(np.max(prob_grid)), 5),
    }


def build_trajectory_geojson(
    all_lons: np.ndarray,
    all_lats: np.ndarray,
    max_tracks: int = 100,
) -> Dict[str, Any]:
    """
    Builds GeoJSON FeatureCollection of LineStrings for backward particle paths.
    all_lons / all_lats shape: (n_particles, n_timesteps)
    """
    n_particles, n_steps = all_lons.shape
    features: List[Dict[str, Any]] = []

    step = max(1, n_particles // max_tracks)
    for i in range(0, n_particles, step):
        coords = []
        for t in range(n_steps):
            x, y = all_lons[i, t], all_lats[i, t]
            if not (np.isnan(x) or np.isnan(y)):
                coords.append([round(float(x), 6), round(float(y), 6)])
        if len(coords) >= 2:
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {"particle_id": i},
            })

    return {"type": "FeatureCollection", "features": features}


def build_particle_timesteps_geojson(
    all_lons: np.ndarray,
    all_lats: np.ndarray,
    detection_time: datetime,
    max_particles: int = 250,
) -> Dict[str, Any]:
    """
    Builds a time-indexed GeoJSON FeatureCollection of Point features.
    Properties include:
    - hour_back: 0 (at detection) to max_duration (e.g. 24)
    - timestamp: ISO-8601 string
    - particle_id: integer

    Enables interactive Mapbox time-slider playback to animate particle drift backward in time.
    """
    n_particles, n_steps = all_lons.shape
    step = max(1, n_particles // max_particles)
    features: List[Dict[str, Any]] = []

    for t in range(n_steps):
        # t=0 is detection time (T-0h); t=1 is T-1h backward, etc.
        hour_back = t
        step_time = (detection_time - timedelta(hours=hour_back)).isoformat()

        for i in range(0, n_particles, step):
            x, y = all_lons[i, t], all_lats[i, t]
            if not (np.isnan(x) or np.isnan(y)):
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(float(x), 6), round(float(y), 6)],
                    },
                    "properties": {
                        "particle_id": i,
                        "hour_back": hour_back,
                        "timestamp": step_time,
                    },
                })

    return {"type": "FeatureCollection", "features": features}
