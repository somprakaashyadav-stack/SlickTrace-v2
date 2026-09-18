"""
SlickTrace v2 — Vessel Trajectory & Behavior Analysis

Calculates comprehensive kinematic and spatial-temporal metrics for candidate AIS vessels:
- mean_sog, min_sog, max_sog, speed_change, acceleration
- mean_cog, course_change, turn_rate
- time_in_origin_zone, distance_to_origin
- ais_gap_count, max_ais_gap_duration, track_completeness, trajectory_length

Detects explainable behavioral and observation anomalies:
- speed reduction
- course change
- unusual turn
- AIS transmission gap (strictly labeled as observation anomaly, never automatic shutdown)
- trajectory deviation
- loitering
- Isolation Forest anomaly scoring with explainable feature contributions
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


def _normalize_positions_dataframe(positions: List[Dict[str, Any]]) -> pd.DataFrame:
    """Normalizes arbitrary position dict keys (e.g. lat/latitude, base_datetime/timestamp_utc)."""
    if not positions:
        return pd.DataFrame(columns=["timestamp_utc", "latitude", "longitude", "sog", "cog", "heading"])

    records = []
    for p in positions:
        # Timestamp normalization
        ts_val = p.get("timestamp_utc") or p.get("base_datetime") or p.get("timestamp")
        if isinstance(ts_val, str):
            ts = pd.to_datetime(ts_val, utc=True, errors="coerce")
        elif isinstance(ts_val, datetime):
            ts = pd.to_datetime(ts_val, utc=True)
        else:
            ts = pd.NaT

        # Lat/Lon normalization
        lat_val = p.get("latitude") if "latitude" in p else p.get("lat")
        lon_val = p.get("longitude") if "longitude" in p else p.get("lon")

        # SOG / COG / Heading
        sog_val = p.get("sog")
        cog_val = p.get("cog")
        heading_val = p.get("heading")

        records.append({
            "timestamp_utc": ts,
            "latitude": float(lat_val) if lat_val is not None and not pd.isna(lat_val) else np.nan,
            "longitude": float(lon_val) if lon_val is not None and not pd.isna(lon_val) else np.nan,
            "sog": float(sog_val) if sog_val is not None and not pd.isna(sog_val) else np.nan,
            "cog": float(cog_val) if cog_val is not None and not pd.isna(cog_val) else np.nan,
            "heading": float(heading_val) if heading_val is not None and not pd.isna(heading_val) else np.nan,
        })

    df = pd.DataFrame(records)
    df = df.dropna(subset=["timestamp_utc", "latitude", "longitude"])
    df = df.sort_values("timestamp_utc").reset_index(drop=True)
    return df


def _circular_mean_degrees(angles_deg: np.ndarray) -> float:
    """Computes circular mean for directional angular quantities (0-360 deg)."""
    valid = angles_deg[~np.isnan(angles_deg)]
    if len(valid) == 0:
        return 0.0
    rads = np.radians(valid)
    sin_sum = np.sum(np.sin(rads))
    cos_sum = np.sum(np.cos(rads))
    mean_rad = math.atan2(sin_sum, cos_sum)
    mean_deg = math.degrees(mean_rad) % 360.0
    return float(mean_deg)


def calculate_trajectory_metrics(
    positions: List[Dict[str, Any]],
    origin_geometry: Optional[Union[BaseGeometry, Dict[str, Any]]] = None,
    gap_threshold_min: float = 15.0,
) -> Dict[str, Any]:
    """
    Calculates exact kinematic and spatial metrics for an AIS trajectory.

    Returns dict with keys:
    - mean_sog (knots)
    - min_sog (knots)
    - max_sog (knots)
    - speed_change (knots)
    - acceleration (knots/min and m/s^2)
    - mean_cog (degrees)
    - course_change (degrees)
    - turn_rate (deg/min)
    - time_in_origin_zone (minutes)
    - distance_to_origin (km)
    - ais_gap_count (int)
    - max_ais_gap_duration (minutes)
    - track_completeness (ratio 0.0 - 1.0)
    - trajectory_length (km)
    - position_count (int)
    - duration_minutes (float)
    """
    df = _normalize_positions_dataframe(positions)

    if len(df) == 0:
        return {
            "mean_sog": 0.0,
            "min_sog": 0.0,
            "max_sog": 0.0,
            "speed_change": 0.0,
            "acceleration": 0.0,
            "acceleration_ms2": 0.0,
            "mean_cog": 0.0,
            "course_change": 0.0,
            "turn_rate": 0.0,
            "time_in_origin_zone": 0.0,
            "distance_to_origin": None,
            "ais_gap_count": 0,
            "max_ais_gap_duration": 0.0,
            "track_completeness": 0.0,
            "trajectory_length": 0.0,
            "position_count": 0,
            "duration_minutes": 0.0,
        }

    sog_arr = df["sog"].fillna(0.0).values.astype(float)
    cog_arr = df["cog"].fillna(0.0).values.astype(float)
    lats = df["latitude"].values
    lons = df["longitude"].values
    times = df["timestamp_utc"]

    # Basic Speed Metrics
    mean_sog = float(np.mean(sog_arr))
    min_sog = float(np.min(sog_arr))
    max_sog = float(np.max(sog_arr))
    speed_change = float(max_sog - min_sog)

    # Basic Course Metrics
    mean_cog = _circular_mean_degrees(cog_arr)

    # Time intervals, step distances, accelerations, turn rates
    n = len(df)
    dt_minutes = np.zeros(max(0, n - 1))
    step_dists_km = np.zeros(max(0, n - 1))
    accelerations_knots_min = np.zeros(max(0, n - 1))
    turn_rates_deg_min = np.zeros(max(0, n - 1))
    angular_diffs_deg = np.zeros(max(0, n - 1))

    for i in range(n - 1):
        t_delta_sec = (times[i + 1] - times[i]).total_seconds()
        dt_min = max(t_delta_sec / 60.0, 1e-6)
        dt_minutes[i] = dt_min

        # Step distance
        dist_km = _haversine_distance_km(lats[i], lons[i], lats[i + 1], lons[i + 1])
        step_dists_km[i] = dist_km

        # Acceleration (knots / minute)
        dv = sog_arr[i + 1] - sog_arr[i]
        accelerations_knots_min[i] = dv / dt_min

        # Course change: smallest angle between two bearings [-180, 180]
        d_cog = (cog_arr[i + 1] - cog_arr[i] + 180.0) % 360.0 - 180.0
        angular_diffs_deg[i] = abs(d_cog)
        turn_rates_deg_min[i] = abs(d_cog) / dt_min

    trajectory_length = float(np.sum(step_dists_km))
    total_course_change = float(np.sum(angular_diffs_deg))
    mean_turn_rate = float(np.mean(turn_rates_deg_min)) if len(turn_rates_deg_min) > 0 else 0.0
    mean_acceleration = float(np.mean(np.abs(accelerations_knots_min))) if len(accelerations_knots_min) > 0 else 0.0

    # Convert acceleration (knots/min) to SI m/s^2 (1 knot = 0.514444 m/s, 1 min = 60 s)
    mean_acceleration_ms2 = float(mean_acceleration * (0.514444 / 60.0))

    # Gap metrics
    gaps = dt_minutes[dt_minutes > gap_threshold_min]
    ais_gap_count = int(len(gaps))
    max_ais_gap_duration = float(np.max(dt_minutes)) if len(dt_minutes) > 0 else 0.0

    total_track_duration_min = float((times.iloc[-1] - times.iloc[0]).total_seconds() / 60.0)
    gap_time_sum = float(np.sum(gaps)) if len(gaps) > 0 else 0.0
    if total_track_duration_min > 0:
        track_completeness = max(0.0, min(1.0, 1.0 - (gap_time_sum / total_track_duration_min)))
    else:
        track_completeness = 1.0

    # Origin zone analysis (if geometry provided)
    origin_poly: Optional[BaseGeometry] = None
    if origin_geometry is not None:
        if isinstance(origin_geometry, dict):
            try:
                origin_poly = shape(origin_geometry)
            except Exception:
                origin_poly = None
        elif isinstance(origin_geometry, BaseGeometry):
            origin_poly = origin_geometry

    time_in_origin_zone = 0.0
    min_dist_to_origin_km: Optional[float] = None

    if origin_poly is not None:
        dists_to_origin = []
        in_zone_flags = np.zeros(n, dtype=bool)
        for i in range(n):
            pt = Point(lons[i], lats[i])
            if origin_poly.contains(pt):
                in_zone_flags[i] = True
                dists_to_origin.append(0.0)
            else:
                # Approximate distance in km from polygon in degrees
                d_deg = origin_poly.distance(pt)
                d_km = d_deg * 111.0  # Approx 1 deg = 111 km
                dists_to_origin.append(d_km)

        if dists_to_origin:
            min_dist_to_origin_km = float(min(dists_to_origin))

        # Time spent inside zone
        for i in range(n - 1):
            if in_zone_flags[i] or in_zone_flags[i + 1]:
                time_in_origin_zone += dt_minutes[i]
    else:
        min_dist_to_origin_km = None
        time_in_origin_zone = 0.0

    return {
        "mean_sog": round(mean_sog, 2),
        "min_sog": round(min_sog, 2),
        "max_sog": round(max_sog, 2),
        "speed_change": round(speed_change, 2),
        "acceleration": round(mean_acceleration, 4),
        "acceleration_ms2": round(mean_acceleration_ms2, 5),
        "mean_cog": round(mean_cog, 1),
        "course_change": round(total_course_change, 1),
        "turn_rate": round(mean_turn_rate, 2),
        "time_in_origin_zone": round(time_in_origin_zone, 1),
        "distance_to_origin": round(min_dist_to_origin_km, 2) if min_dist_to_origin_km is not None else None,
        "ais_gap_count": ais_gap_count,
        "max_ais_gap_duration": round(max_ais_gap_duration, 1),
        "track_completeness": round(track_completeness, 3),
        "trajectory_length": round(trajectory_length, 2),
        "position_count": n,
        "duration_minutes": round(total_track_duration_min, 1),
    }


def detect_trajectory_anomalies(
    positions: List[Dict[str, Any]],
    metrics: Optional[Dict[str, Any]] = None,
    origin_geometry: Optional[Union[BaseGeometry, Dict[str, Any]]] = None,
    reference_sog_mean: Optional[float] = None,
    gap_threshold_min: float = 15.0,
) -> List[Dict[str, Any]]:
    """
    Detects behavioral and observation anomalies across the vessel trajectory:
    1. speed reduction
    2. course change
    3. unusual turn
    4. AIS transmission gap (strictly labeled as observation anomaly, never automatic shutdown)
    5. trajectory deviation
    6. loitering

    Returns a list of structured, explainable anomaly objects.
    """
    df = _normalize_positions_dataframe(positions)
    if len(df) < 2:
        return []

    if metrics is None:
        metrics = calculate_trajectory_metrics(positions, origin_geometry=origin_geometry, gap_threshold_min=gap_threshold_min)

    anomalies: List[Dict[str, Any]] = []

    times = df["timestamp_utc"]
    lats = df["latitude"].values
    lons = df["longitude"].values
    sogs = df["sog"].fillna(0.0).values
    cogs = df["cog"].fillna(0.0).values
    n = len(df)

    mean_sog = metrics.get("mean_sog", float(np.mean(sogs)))
    ref_sog = reference_sog_mean if (reference_sog_mean is not None and reference_sog_mean > 0) else mean_sog

    # 1. AIS Transmission Gaps (Observation Anomaly)
    # IMPORTANT: Never automatically label an AIS gap as intentional shutdown.
    # Show: "AIS transmission gap detected" and provide duration and location.
    for i in range(n - 1):
        dt_min = (times.iloc[i + 1] - times.iloc[i]).total_seconds() / 60.0
        if dt_min >= gap_threshold_min:
            gap_start_ts = times.iloc[i].isoformat()
            gap_end_ts = times.iloc[i + 1].isoformat()
            lat_start, lon_start = float(lats[i]), float(lons[i])
            lat_end, lon_end = float(lats[i + 1]), float(lons[i + 1])
            gap_dist_km = _haversine_distance_km(lat_start, lon_start, lat_end, lon_end)

            anomalies.append({
                "type": "ais_transmission_gap",
                "category": "observation_anomaly",
                "display_label": f"AIS transmission gap detected ({dt_min:.0f} min duration, {gap_dist_km:.1f} km distance)",
                "description": (
                    f"AIS transmission gap detected between {gap_start_ts} and {gap_end_ts}. "
                    f"Gap duration: {dt_min:.1f} minutes. "
                    f"Start location: [{lat_start:.4f}, {lon_start:.4f}], End location: [{lat_end:.4f}, {lon_end:.4f}]. "
                    f"Note: Observation anomaly; does not signify intentional AIS transponder shutdown."
                ),
                "duration_minutes": round(dt_min, 1),
                "location_start": {"latitude": lat_start, "longitude": lon_start},
                "location_end": {"latitude": lat_end, "longitude": lon_end},
                "start_time": gap_start_ts,
                "end_time": gap_end_ts,
                "distance_km": round(gap_dist_km, 2),
                "is_intentional_claim": False,
            })

    # 2. Speed Reduction Anomalies
    min_sog = metrics.get("min_sog", 0.0)
    if ref_sog > 3.0:
        speed_drop_pct = (1.0 - (min_sog / ref_sog)) * 100.0
        if speed_drop_pct >= 40.0:
            # Locate position of minimum speed
            min_idx = int(np.argmin(sogs))
            anomalies.append({
                "type": "speed_reduction",
                "category": "kinematic_anomaly",
                "display_label": f"Speed reduction / drop detected ({min_sog:.1f} kt vs avg {ref_sog:.1f} kt, -{speed_drop_pct:.0f}%)",
                "description": (
                    f"Significant speed reduction / drop detected at {times.iloc[min_idx].isoformat()}. "
                    f"Vessel slowed from baseline {ref_sog:.1f} kt to {min_sog:.1f} kt ({speed_drop_pct:.0f}% reduction)."
                ),
                "min_sog": min_sog,
                "baseline_sog": round(ref_sog, 1),
                "reduction_percentage": round(speed_drop_pct, 1),
                "timestamp": times.iloc[min_idx].isoformat(),
                "location": {"latitude": float(lats[min_idx]), "longitude": float(lons[min_idx])},
            })

    # 3. Course Change & Unusual Turn Anomalies
    max_turn_rate = 0.0
    max_turn_idx = 0
    sharp_turns = []

    for i in range(n - 1):
        dt_min = max((times.iloc[i + 1] - times.iloc[i]).total_seconds() / 60.0, 1e-6)
        d_cog = abs((cogs[i + 1] - cogs[i] + 180.0) % 360.0 - 180.0)
        turn_rate = d_cog / dt_min

        if d_cog >= 45.0 and dt_min <= 30.0:
            sharp_turns.append((i, d_cog, turn_rate, dt_min))

        if turn_rate > max_turn_rate:
            max_turn_rate = turn_rate
            max_turn_idx = i

    if sharp_turns:
        # Report most prominent course change
        sharp_turns.sort(key=lambda x: x[1], reverse=True)
        top_idx, top_dcog, top_rot, top_dt = sharp_turns[0]
        anomalies.append({
            "type": "course_change",
            "category": "navigational_anomaly",
            "display_label": f"Significant course change detected ({top_dcog:.0f}° change)",
            "description": (
                f"Course change of {top_dcog:.1f}° executed over {top_dt:.1f} minutes at {times.iloc[top_idx].isoformat()}. "
                f"Course shifted from {cogs[top_idx]:.0f}° to {cogs[top_idx + 1]:.0f}°."
            ),
            "course_change_deg": round(top_dcog, 1),
            "turn_rate_deg_min": round(top_rot, 2),
            "timestamp": times.iloc[top_idx].isoformat(),
            "location": {"latitude": float(lats[top_idx]), "longitude": float(lons[top_idx])},
        })

    if max_turn_rate >= 15.0:  # > 15 deg/min
        anomalies.append({
            "type": "unusual_turn",
            "category": "navigational_anomaly",
            "display_label": f"Unusual turn rate detected ({max_turn_rate:.1f}°/min)",
            "description": (
                f"Unusual turning maneuver recorded at {times.iloc[max_turn_idx].isoformat()} "
                f"with turn rate of {max_turn_rate:.1f}°/min."
            ),
            "turn_rate_deg_min": round(max_turn_rate, 2),
            "timestamp": times.iloc[max_turn_idx].isoformat(),
            "location": {"latitude": float(lats[max_turn_idx]), "longitude": float(lons[max_turn_idx])},
        })

    # 4. Loitering Anomaly
    # Fraction of time with SOG < 1.5 kt or lingering in small radius
    low_speed_mask = sogs < 1.5
    loiter_fraction = float(np.mean(low_speed_mask))
    if loiter_fraction >= 0.25 and len(df) >= 3:
        loiter_time_min = sum(
            (times.iloc[i + 1] - times.iloc[i]).total_seconds() / 60.0
            for i in range(n - 1) if low_speed_mask[i]
        )
        anomalies.append({
            "type": "loitering",
            "category": "behavioral_anomaly",
            "display_label": f"Vessel loitering detected ({loiter_fraction * 100:.0f}% track time, {loiter_time_min:.0f} min)",
            "description": (
                f"Vessel observed loitering / drifting for approx {loiter_time_min:.1f} minutes "
                f"({loiter_fraction * 100:.0f}% of track at SOG < 1.5 kt)."
            ),
            "loiter_fraction": round(loiter_fraction, 3),
            "loiter_duration_minutes": round(loiter_time_min, 1),
        })

    # 5. Trajectory Deviation (Sinuosity index / detour)
    if n >= 3:
        direct_distance_km = _haversine_distance_km(float(lats[0]), float(lons[0]), float(lats[-1]), float(lons[-1]))
        total_len_km = metrics.get("trajectory_length", 0.0)
        if direct_distance_km > 0.2:
            sinuosity = total_len_km / direct_distance_km
            if sinuosity >= 1.10 and total_len_km >= 1.0:
                anomalies.append({
                    "type": "trajectory_deviation",
                    "category": "navigational_anomaly",
                    "display_label": f"Trajectory deviation detected (sinuosity ratio {sinuosity:.1f}x)",
                    "description": (
                        f"Non-linear track deviation detected. Actual trajectory length is {total_len_km:.1f} km "
                        f"versus direct displacement of {direct_distance_km:.1f} km (sinuosity index: {sinuosity:.2f})."
                    ),
                    "sinuosity_index": round(sinuosity, 2),
                    "actual_distance_km": round(total_len_km, 2),
                    "direct_distance_km": round(direct_distance_km, 2),
                })

    return anomalies



class ExplainableIsolationForest:
    """
    Unsupervised Isolation Forest anomaly scorer tailored for vessel behavior features.
    Provides normalized score (0-1) and human-explainable contribution attribution.
    """

    FEATURE_KEYS = [
        "mean_sog",
        "min_sog",
        "speed_change",
        "acceleration",
        "turn_rate",
        "course_change",
        "ais_gap_count",
        "max_ais_gap_duration",
        "track_completeness",
        "trajectory_length",
    ]

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            random_state=random_state,
        ) if SKLEARN_AVAILABLE else None

    def fit_predict_scores(self, feature_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fits Isolation Forest on candidate feature vectors and returns structured anomaly explanations.
        """
        if not SKLEARN_AVAILABLE or not feature_dicts:
            return [{"isolation_forest_score": 0.5, "top_contributing_features": []} for _ in feature_dicts]

        if len(feature_dicts) < 2:
            return [{"isolation_forest_score": 0.5, "top_contributing_features": ["insufficient_population_for_unsupervised_ranking"]} for _ in feature_dicts]

        X = []
        for fd in feature_dicts:
            row = [float(fd.get(k, 0.0) if fd.get(k) is not None else 0.0) for k in self.FEATURE_KEYS]
            X.append(row)

        X_arr = np.array(X)
        try:
            X_scaled = self.scaler.fit_transform(X_arr)
            self.model.fit(X_scaled)
            raw_scores = self.model.decision_function(X_scaled)

            # Normalize raw scores to 0-1 (1.0 = most anomalous)
            min_s, max_s = raw_scores.min(), raw_scores.max()
            if max_s == min_s:
                norm_scores = np.full(len(feature_dicts), 0.5)
            else:
                norm_scores = 1.0 - (raw_scores - min_s) / (max_s - min_s)

            results = []
            for i, score in enumerate(norm_scores):
                # Identify top contributing features (highest deviation in z-score)
                z_scores = np.abs(X_scaled[i])
                top_indices = np.argsort(z_scores)[::-1][:3]
                top_features = [
                    f"{self.FEATURE_KEYS[idx]} (value={X_arr[i, idx]:.2f}, z-score={z_scores[idx]:.1f})"
                    for idx in top_indices if z_scores[idx] > 1.0
                ]
                results.append({
                    "isolation_forest_score": round(float(score), 3),
                    "top_contributing_features": top_features,
                })
            return results
        except Exception:
            return [{"isolation_forest_score": 0.5, "top_contributing_features": []} for _ in feature_dicts]


def analyze_vessel_trajectory(
    positions: List[Dict[str, Any]],
    origin_geometry: Optional[Union[BaseGeometry, Dict[str, Any]]] = None,
    reference_sog_mean: Optional[float] = None,
    gap_threshold_min: float = 15.0,
) -> Dict[str, Any]:
    """
    Comprehensive pipeline function to calculate metrics, detect anomalies, and generate explanations.
    """
    metrics = calculate_trajectory_metrics(positions, origin_geometry=origin_geometry, gap_threshold_min=gap_threshold_min)
    anomalies = detect_trajectory_anomalies(
        positions,
        metrics=metrics,
        origin_geometry=origin_geometry,
        reference_sog_mean=reference_sog_mean,
        gap_threshold_min=gap_threshold_min,
    )
    named_strings = [a["display_label"] for a in anomalies]

    return {
        "metrics": metrics,
        "anomalies": anomalies,
        "named_anomalies": named_strings,
    }
