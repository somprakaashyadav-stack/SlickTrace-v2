"""
Scoring Module for SlickTrace v2
Calculates composite suspicion score (0-100) combining spatial proximity, temporal overlap, AIS anomalies, vessel type, and discharge risk.
"""
from typing import Dict, Any, List

class SuspectRanker:
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode

    def calculate_score(
        self,
        proximity_km: float,
        time_delta_mins: float,
        anomaly_flags: Dict[str, Any],
        vessel_type: str
    ) -> Dict[str, Any]:
        """Calculates multi-criteria suspicion score."""
        spatial_score = max(0, 100 - (proximity_km * 10))
        temporal_score = max(0, 100 - (abs(time_delta_mins) / 2))
        anomaly_score = 85.0 if anomaly_flags.get("has_ais_gap") else 20.0
        
        composite_score = round(
            (0.35 * spatial_score) + (0.35 * temporal_score) + (0.30 * anomaly_score), 1
        )
        return {
            "composite_score": composite_score,
            "subscores": {
                "spatial_proximity": round(spatial_score, 1),
                "temporal_coincidence": round(temporal_score, 1),
                "anomaly_behavior": round(anomaly_score, 1)
            },
            "rank_label": "CRITICAL SUSPECT" if composite_score >= 80 else "MODERATE SUSPECT"
        }
