"""
SlickTrace v2 — AIS Engine & Anomaly Detection Tests
"""
import pytest
from datetime import datetime, timedelta
from ais.anomaly.detector import extract_track_features, detect_named_anomalies


def test_extract_track_features_normal():
    base = datetime(2026, 9, 16, 8, 0, 0)
    positions = [
        {"base_datetime": (base + timedelta(minutes=10 * i)).isoformat(), "lat": 27.5 + 0.01 * i, "lon": -90.0 + 0.01 * i, "sog": 12.5, "cog": 45.0}
        for i in range(10)
    ]

    features = extract_track_features(positions)
    assert features["mean_sog"] == 12.5
    assert features["max_time_gap_min"] == 10.0
    assert features["ais_gap_count"] == 0.0
    assert features["loiter_fraction"] == 0.0


def test_detect_named_anomalies_with_gap_and_drop():
    base = datetime(2026, 9, 16, 8, 0, 0)
    positions = [
        {"base_datetime": (base + timedelta(minutes=0)).isoformat(), "lat": 27.5, "lon": -90.0, "sog": 14.0, "cog": 45.0},
        {"base_datetime": (base + timedelta(minutes=10)).isoformat(), "lat": 27.51, "lon": -89.99, "sog": 13.5, "cog": 45.0},
        # 40-minute blackout gap and speed drop to 2 knots
        {"base_datetime": (base + timedelta(minutes=50)).isoformat(), "lat": 27.52, "lon": -89.98, "sog": 2.1, "cog": 120.0},
        {"base_datetime": (base + timedelta(minutes=60)).isoformat(), "lat": 27.53, "lon": -89.97, "sog": 13.0, "cog": 50.0},
    ]

    anomalies = detect_named_anomalies(positions, reference_sog_mean=13.8)
    assert any("gap" in a.lower() for a in anomalies)
    assert any("drop" in a.lower() for a in anomalies)
