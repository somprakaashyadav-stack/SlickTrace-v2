"""
SlickTrace v2 — Transparent Candidate Generation with Trajectory & Behavior Analysis

Generates unranked candidate vessels matching spatial-temporal strategies and
performs full kinematic, navigational, and observational anomaly analysis on each candidate track.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import duckdb
import shapely
from shapely.geometry import shape, Point
import json

from ais.query.spatial_query import AISQueryResult, query_vessels_in_origin_window
from ais.ingest.marinecadastre import get_duckdb_connection, AIS_DB_PATH
from ais.trajectory_analysis import (
    analyze_vessel_trajectory,
    calculate_trajectory_metrics,
    detect_trajectory_anomalies,
    ExplainableIsolationForest,
)


class TransparentCandidate:
    def __init__(
        self,
        mmsi: str,
        vessel_name: Optional[str],
        vessel_type: Optional[str],
        observations_count: int,
        first_observation: Optional[datetime],
        last_observation: Optional[datetime],
        minimum_distance_to_origin: Optional[float],
        time_difference: Optional[float],
        track_geometry: Dict[str, Any],
        strategies_matched: List[str],
        trajectory_metrics: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        named_anomalies: List[str],
        isolation_forest_score: float = 0.5,
        isolation_forest_explanations: Optional[List[str]] = None,
        positions_raw: Optional[List[Dict[str, Any]]] = None,
    ):
        self.mmsi = mmsi
        self.vessel_name = vessel_name
        self.vessel_type = vessel_type
        self.observations_count = observations_count
        self.first_observation = first_observation
        self.last_observation = last_observation
        self.minimum_distance_to_origin = minimum_distance_to_origin
        self.time_difference = time_difference
        self.track_geometry = track_geometry
        self.strategies_matched = strategies_matched

        # Kinematic & Trajectory metrics
        self.trajectory_metrics = trajectory_metrics
        self.mean_sog = trajectory_metrics.get("mean_sog")
        self.min_sog = trajectory_metrics.get("min_sog")
        self.max_sog = trajectory_metrics.get("max_sog")
        self.speed_change = trajectory_metrics.get("speed_change")
        self.acceleration = trajectory_metrics.get("acceleration")
        self.acceleration_ms2 = trajectory_metrics.get("acceleration_ms2")
        self.mean_cog = trajectory_metrics.get("mean_cog")
        self.course_change = trajectory_metrics.get("course_change")
        self.turn_rate = trajectory_metrics.get("turn_rate")
        self.time_in_origin_zone = trajectory_metrics.get("time_in_origin_zone")
        self.distance_to_origin = trajectory_metrics.get("distance_to_origin", minimum_distance_to_origin)
        self.ais_gap_count = trajectory_metrics.get("ais_gap_count", 0)
        self.max_ais_gap_duration = trajectory_metrics.get("max_ais_gap_duration", 0.0)
        self.track_completeness = trajectory_metrics.get("track_completeness", 1.0)
        self.trajectory_length = trajectory_metrics.get("trajectory_length", 0.0)

        # Anomalies
        self.anomalies = anomalies
        self.named_anomalies = named_anomalies
        self.isolation_forest_score = isolation_forest_score
        self.isolation_forest_explanations = isolation_forest_explanations or []
        self.positions_raw = positions_raw or []

        # Enforce display requirement: Never label as 'Suspect' before analysis stage
        self.status_display = "Candidate because of observed AIS evidence"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mmsi": self.mmsi,
            "vessel_name": self.vessel_name,
            "vessel_type": self.vessel_type,
            "observations_count": self.observations_count,
            "first_observation": self.first_observation.isoformat() if self.first_observation else None,
            "last_observation": self.last_observation.isoformat() if self.last_observation else None,
            "minimum_distance_to_origin": self.minimum_distance_to_origin,
            "time_difference": self.time_difference,
            "track_geometry": self.track_geometry,
            "strategies_matched": self.strategies_matched,
            "status_display": self.status_display,
            # Trajectory & Behavior metrics
            "mean_sog": self.mean_sog,
            "min_sog": self.min_sog,
            "max_sog": self.max_sog,
            "speed_change": self.speed_change,
            "acceleration": self.acceleration,
            "acceleration_ms2": self.acceleration_ms2,
            "mean_cog": self.mean_cog,
            "course_change": self.course_change,
            "turn_rate": self.turn_rate,
            "time_in_origin_zone": self.time_in_origin_zone,
            "distance_to_origin": self.distance_to_origin,
            "ais_gap_count": self.ais_gap_count,
            "max_ais_gap_duration": self.max_ais_gap_duration,
            "track_completeness": self.track_completeness,
            "trajectory_length": self.trajectory_length,
            "trajectory_metrics": self.trajectory_metrics,
            "anomalies": self.anomalies,
            "named_anomalies": self.named_anomalies,
            "isolation_forest_score": self.isolation_forest_score,
            "isolation_forest_explanations": self.isolation_forest_explanations,
        }


def generate_transparent_candidates(
    origin_geometry: shapely.geometry.base.BaseGeometry,
    time_start: datetime,
    time_end: datetime,
    radius_km: float = 10.0,
    db_path=None,
    gap_threshold_min: float = 15.0,
) -> List[TransparentCandidate]:
    """
    Generate candidates using multiple spatial-temporal strategies without ranking.
    Strategies:
    1. vessel point inside origin polygon
    2. vessel point within configurable radius
    3. vessel observation near high-probability origin cells
    4. temporal overlap
    5. vessel track continuity around the event window

    Calculates trajectory and kinematic behavior metrics for each candidate.
    """
    db_path = db_path or AIS_DB_PATH
    conn = get_duckdb_connection(db_path)

    # Expand the time window by 12h to evaluate track continuity around the event window (Strategy 5)
    expanded_start = time_start - timedelta(hours=12)
    expanded_end = time_end + timedelta(hours=12)

    # Query all vessels in the expanded window and radius
    results, sql = query_vessels_in_origin_window(
        geometry=origin_geometry,
        time_start=expanded_start,
        time_end=expanded_end,
        radius_km=radius_km,
        db_path=db_path,
    )

    pre_candidates = []
    feature_dicts_for_iforest = []

    for res in results:
        strategies = []
        min_dist = float("inf")
        min_time_diff = float("inf")

        coords = []
        first_obs = None
        last_obs = None

        inside_polygon = False
        within_radius = False
        temporal_overlap = False

        for pos in res.positions:
            ts_str = pos.get("timestamp_utc") or pos.get("base_datetime")
            if not ts_str:
                continue

            if isinstance(ts_str, str):
                try:
                    ts = datetime.fromisoformat(ts_str)
                except Exception:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            else:
                ts = ts_str

            if time_start.tzinfo is not None and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            elif time_start.tzinfo is None and ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)

            if not first_obs or ts < first_obs:
                first_obs = ts
            if not last_obs or ts > last_obs:
                last_obs = ts

            lat_val = pos.get("latitude") if "latitude" in pos else pos.get("lat")
            lon_val = pos.get("longitude") if "longitude" in pos else pos.get("lon")
            if lat_val is None or lon_val is None:
                continue

            pt = Point(float(lon_val), float(lat_val))
            coords.append((float(lon_val), float(lat_val)))

            # Strategy 4: Temporal overlap
            if time_start <= ts <= time_end:
                temporal_overlap = True

            # Distance calculation
            try:
                dist_deg = origin_geometry.distance(pt)
                dist_km = dist_deg * 111.0  # Approx km
                if dist_km < min_dist:
                    min_dist = dist_km
            except Exception:
                dist_km = float("inf")

            # Strategy 1 & 2 & 3 evaluations
            if origin_geometry.contains(pt):
                inside_polygon = True
            elif dist_km <= radius_km:
                within_radius = True

            # Time difference to the window
            if ts < time_start:
                td = (time_start - ts).total_seconds()
            elif ts > time_end:
                td = (ts - time_end).total_seconds()
            else:
                td = 0.0

            if td < min_time_diff:
                min_time_diff = td

        # Build strategies list
        if inside_polygon:
            strategies.append("inside_origin_polygon")
        if within_radius:
            strategies.append("within_configurable_radius")
        if temporal_overlap:
            strategies.append("temporal_overlap")
        if min_dist <= radius_km:
            strategies.append("near_high_probability_cells")
        if first_obs and last_obs and first_obs <= time_start and last_obs >= time_end:
            strategies.append("track_continuity_around_window")

        if not strategies:
            continue

        track_geom = {
            "type": "LineString" if len(coords) > 1 else "Point",
            "coordinates": coords if len(coords) > 1 else (coords[0] if coords else []),
        }

        # Trajectory & Behavior Analysis
        analysis = analyze_vessel_trajectory(
            res.positions,
            origin_geometry=origin_geometry,
            gap_threshold_min=gap_threshold_min,
        )

        metrics = analysis["metrics"]
        anomalies = analysis["anomalies"]
        named_anomalies = analysis["named_anomalies"]

        feature_dicts_for_iforest.append(metrics)
        pre_candidates.append({
            "res": res,
            "first_obs": first_obs,
            "last_obs": last_obs,
            "min_dist": min_dist if min_dist != float("inf") else None,
            "min_time_diff": min_time_diff if min_time_diff != float("inf") else None,
            "track_geom": track_geom,
            "strategies": strategies,
            "metrics": metrics,
            "anomalies": anomalies,
            "named_anomalies": named_anomalies,
        })

    # Run Isolation Forest across the candidate population for explainable unsupervised scoring
    iforest = ExplainableIsolationForest()
    iforest_results = iforest.fit_predict_scores(feature_dicts_for_iforest)

    candidates = []
    for item, iforest_res in zip(pre_candidates, iforest_results):
        res = item["res"]
        cand = TransparentCandidate(
            mmsi=res.mmsi,
            vessel_name=res.vessel_name,
            vessel_type=res.vessel_type,
            observations_count=len(res.positions),
            first_observation=item["first_obs"],
            last_observation=item["last_obs"],
            minimum_distance_to_origin=item["min_dist"],
            time_difference=item["min_time_diff"],
            track_geometry=item["track_geom"],
            strategies_matched=item["strategies"],
            trajectory_metrics=item["metrics"],
            anomalies=item["anomalies"],
            named_anomalies=item["named_anomalies"],
            isolation_forest_score=iforest_res["isolation_forest_score"],
            isolation_forest_explanations=iforest_res["top_contributing_features"],
            positions_raw=res.positions,
        )
        candidates.append(cand)

    return candidates


# Convenience alias for candidate generation
generate_candidates = generate_transparent_candidates

