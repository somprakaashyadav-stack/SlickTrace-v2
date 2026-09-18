"""
SlickTrace v2 — Vessel Trajectory & Behavior Analysis Test Suite
"""
import pytest
from datetime import datetime, timedelta, timezone
from shapely.geometry import Polygon, box

from ais.trajectory_analysis import (
    calculate_trajectory_metrics,
    detect_trajectory_anomalies,
    ExplainableIsolationForest,
    analyze_vessel_trajectory,
)


def test_trajectory_metrics_complete_calculation():
    base = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    origin_box = Polygon([[-90.05, 27.45], [-89.95, 27.45], [-89.95, 27.55], [-90.05, 27.55]])

    positions = [
        {"timestamp_utc": (base + timedelta(minutes=0)).isoformat(), "latitude": 27.50, "longitude": -90.00, "sog": 12.0, "cog": 90.0},
        {"timestamp_utc": (base + timedelta(minutes=10)).isoformat(), "latitude": 27.50, "longitude": -89.98, "sog": 10.0, "cog": 90.0},
        {"timestamp_utc": (base + timedelta(minutes=20)).isoformat(), "latitude": 27.50, "longitude": -89.96, "sog": 8.0, "cog": 100.0},
        {"timestamp_utc": (base + timedelta(minutes=30)).isoformat(), "latitude": 27.50, "longitude": -89.94, "sog": 14.0, "cog": 90.0},
    ]

    metrics = calculate_trajectory_metrics(positions, origin_geometry=origin_box, gap_threshold_min=15.0)

    assert metrics["mean_sog"] == 11.0
    assert metrics["min_sog"] == 8.0
    assert metrics["max_sog"] == 14.0
    assert metrics["speed_change"] == 6.0  # 14 - 8
    assert metrics["acceleration"] > 0.0
    assert metrics["mean_cog"] == 92.5
    assert metrics["course_change"] == 20.0  # 0 + 10 + 10
    assert metrics["turn_rate"] > 0.0
    assert metrics["time_in_origin_zone"] > 0.0
    assert metrics["distance_to_origin"] == 0.0  # Inside box initially
    assert metrics["ais_gap_count"] == 0
    assert metrics["max_ais_gap_duration"] == 10.0
    assert metrics["track_completeness"] == 1.0
    assert metrics["trajectory_length"] > 0.0


def test_ais_gap_observation_anomaly_no_automatic_shutdown():
    base = datetime(2026, 9, 16, 6, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp_utc": (base + timedelta(minutes=0)).isoformat(), "latitude": 28.00, "longitude": -91.00, "sog": 14.0, "cog": 45.0},
        {"timestamp_utc": (base + timedelta(minutes=10)).isoformat(), "latitude": 28.02, "longitude": -90.98, "sog": 13.5, "cog": 45.0},
        # 45-minute gap
        {"timestamp_utc": (base + timedelta(minutes=55)).isoformat(), "latitude": 28.10, "longitude": -90.90, "sog": 13.0, "cog": 45.0},
        {"timestamp_utc": (base + timedelta(minutes=65)).isoformat(), "latitude": 28.12, "longitude": -90.88, "sog": 13.2, "cog": 45.0},
    ]

    anomalies = detect_trajectory_anomalies(positions, gap_threshold_min=15.0)
    gap_anomalies = [a for a in anomalies if a["type"] == "ais_transmission_gap"]

    assert len(gap_anomalies) == 1
    gap = gap_anomalies[0]

    # Explicit requirement tests
    assert "AIS transmission gap detected" in gap["display_label"]
    assert gap["duration_minutes"] == 45.0
    assert gap["location_start"]["latitude"] == 28.02
    assert gap["location_start"]["longitude"] == -90.98
    assert gap["location_end"]["latitude"] == 28.10
    assert gap["location_end"]["longitude"] == -90.90
    assert gap["category"] == "observation_anomaly"
    assert gap["is_intentional_claim"] is False
    assert "intentional" not in gap["display_label"].lower()


def test_speed_reduction_and_loitering_anomalies():
    base = datetime(2026, 9, 16, 10, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp_utc": (base + timedelta(minutes=0)).isoformat(), "latitude": 27.50, "longitude": -90.00, "sog": 15.0, "cog": 90.0},
        {"timestamp_utc": (base + timedelta(minutes=10)).isoformat(), "latitude": 27.50, "longitude": -89.98, "sog": 14.0, "cog": 90.0},
        # Drastic speed drop and loitering
        {"timestamp_utc": (base + timedelta(minutes=20)).isoformat(), "latitude": 27.50, "longitude": -89.97, "sog": 0.8, "cog": 120.0},
        {"timestamp_utc": (base + timedelta(minutes=30)).isoformat(), "latitude": 27.501, "longitude": -89.971, "sog": 0.5, "cog": 180.0},
        {"timestamp_utc": (base + timedelta(minutes=40)).isoformat(), "latitude": 27.502, "longitude": -89.972, "sog": 0.6, "cog": 210.0},
    ]

    analysis = analyze_vessel_trajectory(positions, reference_sog_mean=14.5)
    anomalies = analysis["anomalies"]
    types = [a["type"] for a in anomalies]

    assert "speed_reduction" in types
    assert "loitering" in types

    speed_anom = next(a for a in anomalies if a["type"] == "speed_reduction")
    assert speed_anom["min_sog"] == 0.5
    assert speed_anom["reduction_percentage"] > 90.0


def test_course_change_and_unusual_turn_anomalies():
    base = datetime(2026, 9, 16, 14, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp_utc": (base + timedelta(minutes=0)).isoformat(), "latitude": 27.50, "longitude": -90.00, "sog": 12.0, "cog": 0.0},
        {"timestamp_utc": (base + timedelta(minutes=5)).isoformat(), "latitude": 27.52, "longitude": -90.00, "sog": 12.0, "cog": 0.0},
        # Sharp 120 degree turn in 2 minutes -> 60 deg/min turn rate
        {"timestamp_utc": (base + timedelta(minutes=7)).isoformat(), "latitude": 27.53, "longitude": -90.01, "sog": 11.5, "cog": 120.0},
        {"timestamp_utc": (base + timedelta(minutes=15)).isoformat(), "latitude": 27.52, "longitude": -89.98, "sog": 12.0, "cog": 120.0},
    ]

    analysis = analyze_vessel_trajectory(positions)
    types = [a["type"] for a in analysis["anomalies"]]

    assert "course_change" in types
    assert "unusual_turn" in types


def test_trajectory_deviation_sinuosity():
    base = datetime(2026, 9, 16, 16, 0, 0, tzinfo=timezone.utc)
    # S-curve / zigzag trajectory
    positions = [
        {"timestamp_utc": (base + timedelta(minutes=0)).isoformat(), "latitude": 27.00, "longitude": -90.00, "sog": 10.0, "cog": 45.0},
        {"timestamp_utc": (base + timedelta(minutes=10)).isoformat(), "latitude": 27.05, "longitude": -89.90, "sog": 10.0, "cog": 90.0},
        {"timestamp_utc": (base + timedelta(minutes=20)).isoformat(), "latitude": 27.00, "longitude": -89.80, "sog": 10.0, "cog": 180.0},
        {"timestamp_utc": (base + timedelta(minutes=30)).isoformat(), "latitude": 27.05, "longitude": -89.70, "sog": 10.0, "cog": 45.0},
        {"timestamp_utc": (base + timedelta(minutes=40)).isoformat(), "latitude": 27.01, "longitude": -89.60, "sog": 10.0, "cog": 135.0},
    ]

    analysis = analyze_vessel_trajectory(positions)
    types = [a["type"] for a in analysis["anomalies"]]
    assert "trajectory_deviation" in types


def test_isolation_forest_explainability():
    # Fleet with 3 normal vessels and 1 anomalous vessel
    normal_v1 = {"mean_sog": 13.0, "min_sog": 12.5, "speed_change": 1.0, "acceleration": 0.05, "turn_rate": 1.0, "course_change": 5.0, "ais_gap_count": 0, "max_ais_gap_duration": 5.0, "track_completeness": 1.0, "trajectory_length": 50.0}
    normal_v2 = {"mean_sog": 12.8, "min_sog": 12.0, "speed_change": 1.5, "acceleration": 0.06, "turn_rate": 1.2, "course_change": 8.0, "ais_gap_count": 0, "max_ais_gap_duration": 6.0, "track_completeness": 1.0, "trajectory_length": 48.0}
    normal_v3 = {"mean_sog": 13.2, "min_sog": 12.7, "speed_change": 1.2, "acceleration": 0.04, "turn_rate": 0.8, "course_change": 6.0, "ais_gap_count": 0, "max_ais_gap_duration": 5.0, "track_completeness": 1.0, "trajectory_length": 52.0}
    anomalous_v = {"mean_sog": 4.0, "min_sog": 0.2, "speed_change": 14.0, "acceleration": 1.5, "turn_rate": 25.0, "course_change": 180.0, "ais_gap_count": 3, "max_ais_gap_duration": 75.0, "track_completeness": 0.4, "trajectory_length": 15.0}

    fleet = [normal_v1, normal_v2, normal_v3, anomalous_v]
    scorer = ExplainableIsolationForest(contamination=0.25)
    results = scorer.fit_predict_scores(fleet)

    assert len(results) == 4
    # Anomalous vessel should have highest anomaly score
    scores = [r["isolation_forest_score"] for r in results]
    assert scores[3] > scores[0]
    assert scores[3] > scores[1]
    assert scores[3] > scores[2]
    # Check explainability
    assert len(results[3]["top_contributing_features"]) > 0
