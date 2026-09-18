"""
SlickTrace v2 — Physical Consistency Ranking Engine Test Suite
"""
import pytest
from datetime import datetime, timedelta, timezone
from shapely.geometry import Polygon, Point

from ais.ranking_engine import (
    PhysicalConsistencyScorer,
    rank_candidates,
    PHYSICAL_CONSISTENCY_DISCLAIMER,
)


def test_physical_consistency_scorer_all_10_factors():
    base = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    origin_poly = Polygon([[-90.1, 27.4], [-89.9, 27.4], [-89.9, 27.6], [-90.1, 27.6]])
    origin_centroid = (27.50, -90.00)
    time_window = (base - timedelta(hours=2), base + timedelta(hours=2))
    spill_loc = (27.70, -89.80)

    # Candidate track passing right through origin polygon during the time window
    candidate_positions = [
        {"timestamp_utc": (base - timedelta(minutes=30)).isoformat(), "latitude": 27.45, "longitude": -90.05, "sog": 12.0, "cog": 45.0},
        {"timestamp_utc": (base).isoformat(), "latitude": 27.50, "longitude": -90.00, "sog": 8.0, "cog": 45.0},
        {"timestamp_utc": (base + timedelta(minutes=30)).isoformat(), "latitude": 27.55, "longitude": -89.95, "sog": 12.0, "cog": 45.0},
    ]

    scorer = PhysicalConsistencyScorer()
    res = scorer.evaluate_candidate(
        candidate_positions=candidate_positions,
        hindcast_origin_geometry=origin_poly,
        hindcast_origin_centroid=origin_centroid,
        hindcast_time_window=time_window,
        spill_detection_location=spill_loc,
        vessel_type="Crude Oil Tanker",
        counterfactual_result={"counterfactual_consistent": True},
        isolation_forest_score=0.75,
    )

    # Name and terminology tests
    assert res.score >= 70.0
    assert res.physical_consistency_score == res.score
    assert res.investigation_consistency_score == res.score
    assert 0.0 <= res.confidence <= 1.0

    # Verify all 10 required factors are calculated in feature_values
    fvals = res.feature_values
    assert "spatial_consistency" in fvals
    assert "temporal_consistency" in fvals
    assert "origin_proximity" in fvals
    assert "time_in_origin_zone" in fvals
    assert "drift_consistency" in fvals
    assert "trajectory_consistency" in fvals
    assert "speed_behavior_consistency" in fvals
    assert "course_behavior_consistency" in fvals
    assert "AIS_continuity" in fvals
    assert "counterfactual_similarity" in fvals

    # Verify feature contributions structure
    factors_in_contributions = {c["factor"] for c in res.feature_contributions}
    assert "origin_proximity" in factors_in_contributions
    assert "spatial_consistency" in factors_in_contributions
    assert "temporal_consistency" in factors_in_contributions

    for c in res.feature_contributions:
        assert "factor" in c
        assert "value" in c
        assert "contribution" in c
        assert "explanation" in c
        assert len(c["explanation"]) > 0

    # Verify scoring mode is transparent when XGBoost weights are missing (no fabrication)
    assert "TRANSPARENT_RULE_BASED" in res.scoring_mode
    assert "XGBoost weights unavailable" in res.scoring_mode

    # Verify mandatory disclaimer
    assert PHYSICAL_CONSISTENCY_DISCLAIMER in res.limitations
    assert res.disclaimer == "This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility."


def test_rank_candidates_sorting_after_all_evidence():
    base = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    origin_poly = Polygon([[-90.1, 27.4], [-89.9, 27.4], [-89.9, 27.6], [-90.1, 27.6]])
    origin_centroid = (27.50, -90.00)
    time_window = (base - timedelta(hours=1), base + timedelta(hours=1))

    # Close candidate (inside origin)
    close_cand = {
        "mmsi": "111222333",
        "vessel_name": "Vessel High Consistency",
        "vessel_type": "Tanker",
        "positions_raw": [
            {"timestamp_utc": base.isoformat(), "latitude": 27.50, "longitude": -90.00, "sog": 10.0, "cog": 45.0},
        ],
    }

    # Far candidate (100km away)
    far_cand = {
        "mmsi": "999888777",
        "vessel_name": "Vessel Distant",
        "vessel_type": "Cargo",
        "positions_raw": [
            {"timestamp_utc": base.isoformat(), "latitude": 28.50, "longitude": -90.00, "sog": 14.0, "cog": 45.0},
        ],
    }

    ranked = rank_candidates(
        candidates_data=[far_cand, close_cand],  # Input in random order
        hindcast_origin_geometry=origin_poly,
        hindcast_origin_centroid=origin_centroid,
        hindcast_time_window=time_window,
    )

    assert len(ranked) == 2
    # Candidate with closest passage must be ranked #1
    assert ranked[0]["mmsi"] == "111222333"
    assert ranked[0]["rank"] == 1
    assert ranked[1]["mmsi"] == "999888777"
    assert ranked[1]["rank"] == 2
    assert ranked[0]["physical_score"] > ranked[1]["physical_score"]
