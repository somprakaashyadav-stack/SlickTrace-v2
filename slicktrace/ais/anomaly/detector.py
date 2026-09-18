"""
SlickTrace v2 — Vessel Anomaly Detection (Isolation Forest & Heuristics)

Detects behavioral and observational anomalies in vessel AIS tracks:
- Speed drops and kinematic changes
- Course changes and unusual turns
- AIS transmission gaps (strictly observation anomalies, never automatic shutdown assumptions)
- Loitering and trajectory deviations
- Isolation Forest unsupervised anomaly scoring with explainable contributions
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from ais.trajectory_analysis import (
    calculate_trajectory_metrics,
    detect_trajectory_anomalies,
    ExplainableIsolationForest,
    analyze_vessel_trajectory,
    _normalize_positions_dataframe,
)

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AnomalyDetectionError(Exception):
    pass


def extract_track_features(positions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extract comprehensive behavioral & kinematic features from a vessel's AIS track positions.

    Supports both legacy keys ('lat', 'lon', 'base_datetime') and normalized keys
    ('latitude', 'longitude', 'timestamp_utc').
    """
    if not positions:
        return _empty_features()

    metrics = calculate_trajectory_metrics(positions)
    df = _normalize_positions_dataframe(positions)
    sog_arr = df["sog"].fillna(0.0).values if len(df) > 0 else np.array([])
    mean_sog = metrics["mean_sog"]
    min_sog = metrics["min_sog"]
    std_sog = float(np.std(sog_arr)) if len(sog_arr) > 0 else 0.0

    loiter_fraction = float(np.mean(sog_arr < 1.0)) if len(sog_arr) > 0 else 0.0
    sog_drop_ratio = float(min_sog / (mean_sog + 1e-9))

    return {
        "mean_sog": float(metrics["mean_sog"]),
        "min_sog": float(metrics["min_sog"]),
        "max_sog": float(metrics["max_sog"]),
        "std_sog": float(std_sog),
        "speed_change": float(metrics["speed_change"]),
        "acceleration": float(metrics["acceleration"]),
        "acceleration_ms2": float(metrics["acceleration_ms2"]),
        "mean_cog": float(metrics["mean_cog"]),
        "course_change": float(metrics["course_change"]),
        "turn_rate": float(metrics["turn_rate"]),
        "heading_change_deg": float(metrics["course_change"]),
        "max_time_gap_min": float(metrics["max_ais_gap_duration"]),
        "ais_gap_count": float(metrics["ais_gap_count"]),
        "track_completeness": float(metrics["track_completeness"]),
        "trajectory_length": float(metrics["trajectory_length"]),
        "sog_drop_ratio": float(sog_drop_ratio),
        "loiter_fraction": float(loiter_fraction),
        "position_count": float(metrics["position_count"]),
        "duration_minutes": float(metrics["duration_minutes"]),
    }


def _empty_features() -> Dict[str, float]:
    return {
        "mean_sog": 0.0,
        "min_sog": 0.0,
        "max_sog": 0.0,
        "std_sog": 0.0,
        "speed_change": 0.0,
        "acceleration": 0.0,
        "acceleration_ms2": 0.0,
        "mean_cog": 0.0,
        "course_change": 0.0,
        "turn_rate": 0.0,
        "heading_change_deg": 0.0,
        "max_time_gap_min": 0.0,
        "ais_gap_count": 0.0,
        "track_completeness": 0.0,
        "trajectory_length": 0.0,
        "sog_drop_ratio": 0.0,
        "loiter_fraction": 0.0,
        "position_count": 0.0,
        "duration_minutes": 0.0,
    }


FEATURE_NAMES = list(_empty_features().keys())


def detect_anomalies(
    vessel_features: List[Dict[str, float]],
    contamination: float = 0.1,
) -> List[float]:
    """
    Run Isolation Forest on a list of vessel feature dicts.
    Returns list of float anomaly scores (higher = more anomalous, range 0-1).
    """
    if not SKLEARN_AVAILABLE:
        raise AnomalyDetectionError(
            "scikit-learn not installed. pip install scikit-learn"
        )

    if not vessel_features:
        return []

    scorer = ExplainableIsolationForest(contamination=contamination)
    results = scorer.fit_predict_scores(vessel_features)
    return [r["isolation_forest_score"] for r in results]


def detect_named_anomalies(
    positions: List[Dict[str, Any]],
    reference_sog_mean: Optional[float] = None,
) -> List[str]:
    """
    Return human-readable anomaly descriptions for a single vessel's track.

    Guarantees that AIS gaps are presented as observation anomalies and never
    automatically labeled as intentional shutdowns.
    """
    analysis = analyze_vessel_trajectory(positions, reference_sog_mean=reference_sog_mean)
    return analysis["named_anomalies"]
