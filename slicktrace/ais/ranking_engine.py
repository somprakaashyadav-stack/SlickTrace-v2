"""
SlickTrace v2 — Core Physical Consistency Ranking Engine

Evaluates and ranks candidate vessels against reconstructed ocean-physics hindcast scenarios.
Strict Terminology:
- Primary Name: "Physical Consistency Score"
- Secondary Name: "Investigation Consistency Score"
- Prohibited Term: Never call or label this a "guilt score".

Mandatory UI / Report Notice:
"This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility."

Calculates 10 Core Physical Consistency Factors:
1. spatial_consistency
2. temporal_consistency
3. origin_proximity
4. time_in_origin_zone
5. drift_consistency
6. trajectory_consistency
7. speed_behavior_consistency
8. course_behavior_consistency
9. AIS_continuity
10. counterfactual_similarity

Scoring Modes:
- "XGBOOST_TRAINED_MODEL": Used when calibrated model weights exist on disk.
- "TRANSPARENT_RULE_BASED": Transparent, auditable weighted aggregation used when trained ML weights are unavailable (no fabricated ML predictions).
- "ISOLATION_FOREST_ANOMALY": Unsupervised anomaly feature integration.
"""
from __future__ import annotations

import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from shapely.geometry import Point, Polygon, shape
from shapely.geometry.base import BaseGeometry

from ais.trajectory_analysis import (
    calculate_trajectory_metrics,
    detect_trajectory_anomalies,
    ExplainableIsolationForest,
    _haversine_distance_km,
)

# Standard disclaimer strictly required across UI and reporting
PHYSICAL_CONSISTENCY_DISCLAIMER = (
    "This score measures consistency with the reconstructed physical scenario. "
    "It is not a determination of responsibility."
)

DEFAULT_WEIGHTS = {
    "origin_proximity": 0.20,
    "spatial_consistency": 0.15,
    "temporal_consistency": 0.15,
    "drift_consistency": 0.12,
    "time_in_origin_zone": 0.08,
    "trajectory_consistency": 0.08,
    "speed_behavior_consistency": 0.06,
    "course_behavior_consistency": 0.06,
    "AIS_continuity": 0.05,
    "counterfactual_similarity": 0.05,
}


@dataclass
class FactorContribution:
    factor: str
    value: Union[float, int, str, None]
    contribution: float
    explanation: str
    weight: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor,
            "value": self.value,
            "contribution": round(self.contribution, 4),
            "weight": round(self.weight, 4),
            "explanation": self.explanation,
        }


@dataclass
class PhysicalConsistencyResult:
    score: float  # 0.0 - 100.0
    investigation_consistency_score: float  # 0.0 - 100.0 (synonym)
    confidence: float  # 0.0 - 1.0
    scoring_mode: str  # TRANSPARENT_RULE_BASED | XGBOOST_TRAINED_MODEL
    feature_values: Dict[str, Any]
    feature_contributions: List[Dict[str, Any]]
    explanation: str
    limitations: List[str]
    disclaimer: str = PHYSICAL_CONSISTENCY_DISCLAIMER

    @property
    def physical_consistency_score(self) -> float:
        return self.score


    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "physical_consistency_score": round(self.score, 1),
            "investigation_consistency_score": round(self.investigation_consistency_score, 1),
            "confidence": round(self.confidence, 3),
            "scoring_mode": self.scoring_mode,
            "feature_values": self.feature_values,
            "feature_contributions": self.feature_contributions,
            "explanation": self.explanation,
            "limitations": self.limitations,
            "disclaimer": self.disclaimer,
        }


def _calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates initial compass bearing from (lat1, lon1) to (lat2, lon2) in degrees (0-360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return float((bearing + 360.0) % 360.0)


def _angular_difference_deg(angle1: float, angle2: float) -> float:
    """Returns minimum angular difference between two bearings in degrees (0 to 180)."""
    diff = abs(angle1 - angle2) % 360.0
    return float(360.0 - diff if diff > 180.0 else diff)


class PhysicalConsistencyScorer:
    """
    Computes explainable Physical Consistency Scores for candidate vessels
    against Lagrangian hindcast origin regions and environmental forcing.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        weights_dir: Optional[Union[str, Path]] = None,
    ):
        self.weights = weights or DEFAULT_WEIGHTS
        # Normalize weights to sum to 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

        self.weights_dir = Path(weights_dir) if weights_dir else Path("ml/weights")
        self.xgb_model = None
        self._load_xgboost_if_available()

    def _load_xgboost_if_available(self) -> None:
        """Loads trained XGBoost model if weights exist on disk. Never fabricates."""
        xgb_path = self.weights_dir / "consistency_ranker.json"
        if not xgb_path.exists():
            xgb_path = self.weights_dir / "consistency_ranker.xgb"

        if xgb_path.exists():
            try:
                import xgboost as xgb
                self.xgb_model = xgb.Booster()
                self.xgb_model.load_model(str(xgb_path))
            except Exception:
                self.xgb_model = None

    def evaluate_candidate(
        self,
        candidate_positions: List[Dict[str, Any]],
        hindcast_origin_geometry: Optional[Union[BaseGeometry, Dict[str, Any]]],
        hindcast_origin_centroid: Optional[Tuple[float, float]],  # (lat, lon)
        hindcast_time_window: Tuple[datetime, datetime],  # (start_utc, end_utc)
        spill_detection_location: Optional[Tuple[float, float]] = None,  # (lat, lon)
        spill_detection_time: Optional[datetime] = None,
        vessel_type: Optional[str] = None,
        counterfactual_result: Optional[Dict[str, Any]] = None,
        isolation_forest_score: Optional[float] = None,
    ) -> PhysicalConsistencyResult:
        """
        Calculates all 10 physical consistency factors, factor contributions, explainability,
        and limitations for an individual candidate vessel.
        """
        metrics = calculate_trajectory_metrics(candidate_positions, origin_geometry=hindcast_origin_geometry)
        anomalies = detect_trajectory_anomalies(candidate_positions, metrics=metrics, origin_geometry=hindcast_origin_geometry)

        origin_start, origin_end = hindcast_time_window
        origin_poly = shape(hindcast_origin_geometry) if isinstance(hindcast_origin_geometry, dict) else hindcast_origin_geometry

        # 1. origin_proximity (Distance to reconstructed origin centroid/polygon)
        min_dist_km = metrics.get("distance_to_origin")
        if min_dist_km is None and hindcast_origin_centroid and candidate_positions:
            c_lat, c_lon = hindcast_origin_centroid
            dists = []
            for p in candidate_positions:
                lat = p.get("latitude") if "latitude" in p else p.get("lat")
                lon = p.get("longitude") if "longitude" in p else p.get("lon")
                if lat is not None and lon is not None:
                    dists.append(_haversine_distance_km(float(lat), float(lon), c_lat, c_lon))
            min_dist_km = min(dists) if dists else 50.0

        if min_dist_km is None:
            min_dist_km = 50.0

        # Score: 1.0 at 0km, decays smoothly over 50km
        origin_proximity_score = max(0.0, min(1.0, math.exp(-min_dist_km / 12.0)))

        # 2. spatial_consistency (Intersection with probability polygon envelopes)
        in_polygon = False
        if origin_poly and candidate_positions:
            for p in candidate_positions:
                lat = p.get("latitude") if "latitude" in p else p.get("lat")
                lon = p.get("longitude") if "longitude" in p else p.get("lon")
                if lat is not None and lon is not None and origin_poly.contains(Point(float(lon), float(lat))):
                    in_polygon = True
                    break

        if in_polygon:
            spatial_consistency_score = 1.0
        elif min_dist_km <= 5.0:
            spatial_consistency_score = max(0.0, 1.0 - (min_dist_km / 15.0))
        else:
            spatial_consistency_score = max(0.0, math.exp(-min_dist_km / 25.0))

        # 3. temporal_consistency (Overlap with estimated release window)
        # Find closest observation timestamp to release window
        min_time_diff_sec = float("inf")
        has_temporal_overlap = False
        for p in candidate_positions:
            ts_raw = p.get("timestamp_utc") or p.get("base_datetime")
            if not ts_raw:
                continue
            if isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    ts = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
            else:
                ts = ts_raw

            if origin_start.tzinfo is not None and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            elif origin_start.tzinfo is None and ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)

            if origin_start <= ts <= origin_end:
                has_temporal_overlap = True
                min_time_diff_sec = 0.0
                break
            elif ts < origin_start:
                diff = (origin_start - ts).total_seconds()
            else:
                diff = (ts - origin_end).total_seconds()
            min_time_diff_sec = min(min_time_diff_sec, diff)

        time_diff_hours = min_time_diff_sec / 3600.0 if min_time_diff_sec != float("inf") else 24.0
        if has_temporal_overlap:
            temporal_consistency_score = 1.0
        else:
            temporal_consistency_score = max(0.0, math.exp(-time_diff_hours / 4.0))

        # 4. time_in_origin_zone (Dwell time inside probability zone)
        time_in_zone_min = metrics.get("time_in_origin_zone", 0.0)
        # Score increases up to 30 mins dwell time
        if time_in_zone_min >= 20.0:
            time_in_zone_score = 1.0
        elif time_in_zone_min > 0.0:
            time_in_zone_score = 0.5 + 0.5 * (time_in_zone_min / 20.0)
        elif min_dist_km <= 5.0:
            time_in_zone_score = 0.3
        else:
            time_in_zone_score = 0.05

        # 5. drift_consistency (Vector alignment between candidate release point & observed spill)
        drift_consistency_score = 0.5  # Neutral default
        drift_explanation_extra = ""
        if spill_detection_location and hindcast_origin_centroid:
            c_lat, c_lon = hindcast_origin_centroid
            spill_lat, spill_lon = spill_detection_location
            # Theoretical drift vector from origin centroid to spill location
            expected_drift_bearing = _calculate_bearing_deg(c_lat, c_lon, spill_lat, spill_lon)

            # Candidate bearing from closest approach to spill location
            cand_bearing = expected_drift_bearing
            if candidate_positions:
                closest_p = min(
                    candidate_positions,
                    key=lambda p: _haversine_distance_km(
                        float(p.get("latitude", p.get("lat", 0))),
                        float(p.get("longitude", p.get("lon", 0))),
                        c_lat,
                        c_lon,
                    ),
                )
                p_lat = float(closest_p.get("latitude", closest_p.get("lat", 0)))
                p_lon = float(closest_p.get("longitude", closest_p.get("lon", 0)))
                cand_bearing = _calculate_bearing_deg(p_lat, p_lon, spill_lat, spill_lon)

            bearing_err = _angular_difference_deg(expected_drift_bearing, cand_bearing)
            # Alignment score: 1.0 at 0 deg diff, 0.0 at 180 deg
            drift_consistency_score = max(0.0, (1.0 + math.cos(math.radians(bearing_err))) / 2.0)
            drift_explanation_extra = f" (drift vector alignment deviation: {bearing_err:.1f}°)"

        # 6. trajectory_consistency (Trajectory path intersects / crosses origin envelope)
        mean_cog = metrics.get("mean_cog", 0.0)
        traj_len = metrics.get("trajectory_length", 0.0)
        if in_polygon:
            trajectory_consistency_score = 0.95
        elif min_dist_km <= 5.0:
            trajectory_consistency_score = 0.80
        elif min_dist_km <= 15.0:
            trajectory_consistency_score = 0.50
        else:
            trajectory_consistency_score = max(0.05, math.exp(-min_dist_km / 20.0))

        # 7. speed_behavior_consistency (Kinematic speed change / maneuvering)
        mean_sog = metrics.get("mean_sog", 10.0)
        min_sog = metrics.get("min_sog", 10.0)
        speed_change = metrics.get("speed_change", 0.0)
        has_speed_drop = any(a["type"] == "speed_reduction" for a in anomalies)
        has_loitering = any(a["type"] == "loitering" for a in anomalies)

        if has_loitering or (has_speed_drop and in_polygon):
            speed_behavior_score = 0.90
        elif has_speed_drop or speed_change >= 4.0:
            speed_behavior_score = 0.75
        elif 6.0 <= mean_sog <= 16.0:  # Normal commercial cruising speed
            speed_behavior_score = 0.60
        else:
            speed_behavior_score = 0.40

        # 8. course_behavior_consistency (Course changes, turning maneuvers)
        has_course_change = any(a["type"] == "course_change" for a in anomalies)
        has_unusual_turn = any(a["type"] == "unusual_turn" for a in anomalies)
        has_traj_deviation = any(a["type"] == "trajectory_deviation" for a in anomalies)

        if has_unusual_turn or (has_course_change and in_polygon):
            course_behavior_score = 0.88
        elif has_course_change or has_traj_deviation:
            course_behavior_score = 0.72
        else:
            course_behavior_score = 0.50

        # 9. AIS_continuity (Observation completeness & gap handling)
        # Note: Gaps are strictly observation anomalies. High gap duration near origin zone
        # increases observational uncertainty and consistency with unobserved window.
        ais_gap_count = metrics.get("ais_gap_count", 0)
        max_gap_min = metrics.get("max_ais_gap_duration", 0.0)
        has_gap_anomaly = any(a["type"] == "ais_transmission_gap" for a in anomalies)

        if has_gap_anomaly and (in_polygon or min_dist_km <= 10.0):
            ais_continuity_score = 0.85  # Observation gap coincides with origin region
        elif has_gap_anomaly:
            ais_continuity_score = 0.65
        else:
            ais_continuity_score = 0.50  # Steady transmission

        # 10. counterfactual_similarity (Forward verification)
        counterfactual_score = 0.50  # Neutral baseline
        cf_explanation = "Forward counterfactual simulation pending or baseline projection used."
        if counterfactual_result:
            if counterfactual_result.get("counterfactual_consistent") is True:
                counterfactual_score = 0.95
                cf_explanation = "Forward Lagrangian particle simulation from vessel position successfully recreated observed slick."
            elif counterfactual_result.get("counterfactual_consistent") is False:
                counterfactual_score = 0.15
                cf_explanation = "Forward simulation from candidate track diverged significantly from observed slick polygon."
            elif "similarity" in counterfactual_result:
                counterfactual_score = float(counterfactual_result["similarity"])
                cf_explanation = f"Forward simulation yielded {counterfactual_score*100:.1f}% spatial similarity."

        # Compile feature values dictionary
        feature_values = {
            "origin_proximity": round(origin_proximity_score, 4),
            "spatial_consistency": round(spatial_consistency_score, 4),
            "temporal_consistency": round(temporal_consistency_score, 4),
            "drift_consistency": round(drift_consistency_score, 4),
            "time_in_origin_zone": round(time_in_zone_score, 4),
            "trajectory_consistency": round(trajectory_consistency_score, 4),
            "speed_behavior_consistency": round(speed_behavior_score, 4),
            "course_behavior_consistency": round(course_behavior_score, 4),
            "AIS_continuity": round(ais_continuity_score, 4),
            "counterfactual_similarity": round(counterfactual_score, 4),
            # Raw supporting metrics
            "minimum_distance_km": round(min_dist_km, 2),
            "time_in_origin_zone_minutes": round(time_in_zone_min, 1),
            "time_offset_hours": round(time_diff_hours, 2),
            "mean_sog_knots": metrics.get("mean_sog"),
            "ais_gap_count": ais_gap_count,
            "max_ais_gap_minutes": max_gap_min,
            "isolation_forest_score": round(isolation_forest_score, 4) if isolation_forest_score is not None else 0.5,
        }

        # Build explainable feature contributions
        contributions: List[FactorContribution] = [
            FactorContribution(
                factor="origin_proximity",
                value=f"{min_dist_km:.1f} km closest approach",
                contribution=origin_proximity_score * self.weights["origin_proximity"] * 100.0,
                weight=self.weights["origin_proximity"],
                explanation=(
                    f"AIS observations place the vessel within {min_dist_km:.1f} km of the reconstructed origin centroid."
                    if min_dist_km > 0.1
                    else "AIS observations place the vessel directly at the reconstructed origin centroid."
                ),
            ),
            FactorContribution(
                factor="spatial_consistency",
                value="Inside origin polygon" if in_polygon else f"{min_dist_km:.1f} km from boundary",
                contribution=spatial_consistency_score * self.weights["spatial_consistency"] * 100.0,
                weight=self.weights["spatial_consistency"],
                explanation=(
                    "Vessel trajectory intersects the highest-probability (P50/P75) origin probability envelope."
                    if in_polygon
                    else f"Vessel track passed within {min_dist_km:.1f} km of the origin probability envelope boundary."
                ),
            ),
            FactorContribution(
                factor="temporal_consistency",
                value="Direct window overlap" if has_temporal_overlap else f"{time_diff_hours:.1f} h offset",
                contribution=temporal_consistency_score * self.weights["temporal_consistency"] * 100.0,
                weight=self.weights["temporal_consistency"],
                explanation=(
                    f"Vessel was actively present in the region during the estimated release window ({origin_start.strftime('%H:%M')} - {origin_end.strftime('%H:%M')} UTC)."
                    if has_temporal_overlap
                    else f"Vessel passage occurred {time_diff_hours:.1f} hours from the estimated release window."
                ),
            ),
            FactorContribution(
                factor="drift_consistency",
                value=f"{drift_consistency_score*100:.0f}% alignment",
                contribution=drift_consistency_score * self.weights["drift_consistency"] * 100.0,
                weight=self.weights["drift_consistency"],
                explanation=f"Trajectory displacement vector aligns with environmental drift forcing{drift_explanation_extra}.",
            ),
            FactorContribution(
                factor="time_in_origin_zone",
                value=f"{time_in_zone_min:.1f} minutes",
                contribution=time_in_zone_score * self.weights["time_in_origin_zone"] * 100.0,
                weight=self.weights["time_in_origin_zone"],
                explanation=f"Vessel spent approximately {time_in_zone_min:.1f} minutes within the probable origin zone boundary.",
            ),
            FactorContribution(
                factor="trajectory_consistency",
                value=f"{metrics.get('trajectory_length', 0):.1f} km path length",
                contribution=trajectory_consistency_score * self.weights["trajectory_consistency"] * 100.0,
                weight=self.weights["trajectory_consistency"],
                explanation="Vessel heading and continuous course geometry intersect the drift corridor.",
            ),
            FactorContribution(
                factor="speed_behavior_consistency",
                value=f"Mean {metrics.get('mean_sog', 0):.1f} kt (min {metrics.get('min_sog', 0):.1f} kt)",
                contribution=speed_behavior_score * self.weights["speed_behavior_consistency"] * 100.0,
                weight=self.weights["speed_behavior_consistency"],
                explanation=(
                    "Speed profile exhibits significant speed reduction / loitering in the origin zone."
                    if (has_speed_drop or has_loitering)
                    else "Vessel speed profile is consistent with standard steady-state passage."
                ),
            ),
            FactorContribution(
                factor="course_behavior_consistency",
                value=f"Course variation {metrics.get('course_change', 0):.0f}°",
                contribution=course_behavior_score * self.weights["course_behavior_consistency"] * 100.0,
                weight=self.weights["course_behavior_consistency"],
                explanation=(
                    "Navigational maneuvers (heading changes / turns) recorded near the event window."
                    if (has_course_change or has_unusual_turn)
                    else "Vessel maintained a steady linear course without sharp turns."
                ),
            ),
            FactorContribution(
                factor="AIS_continuity",
                value=f"{ais_gap_count} observation gaps (max {max_gap_min:.0f} min)" if ais_gap_count > 0 else "Continuous transmission",
                contribution=ais_continuity_score * self.weights["AIS_continuity"] * 100.0,
                weight=self.weights["AIS_continuity"],
                explanation=(
                    f"AIS transmission gap of {max_gap_min:.0f} min detected in proximity to origin zone (observation anomaly; no intentional shutdown assumed)."
                    if has_gap_anomaly
                    else "Continuous AIS transmission received throughout the origin passage window."
                ),
            ),
            FactorContribution(
                factor="counterfactual_similarity",
                value=f"{counterfactual_score*100:.0f}% match",
                contribution=counterfactual_score * self.weights["counterfactual_similarity"] * 100.0,
                weight=self.weights["counterfactual_similarity"],
                explanation=cf_explanation,
            ),
        ]

        # Compute composite Physical Consistency Score
        if self.xgb_model is not None:
            scoring_mode = "XGBOOST_TRAINED_MODEL"
            try:
                import xgboost as xgb
                feat_vec = np.array([[
                    origin_proximity_score,
                    spatial_consistency_score,
                    temporal_consistency_score,
                    drift_consistency_score,
                    time_in_zone_score,
                    trajectory_consistency_score,
                    speed_behavior_score,
                    course_behavior_score,
                    ais_continuity_score,
                    counterfactual_score,
                    isolation_forest_score or 0.5,
                ]])
                dmat = xgb.DMatrix(feat_vec)
                raw_pred = float(self.xgb_model.predict(dmat)[0])
                final_score = max(0.0, min(100.0, raw_pred * 100.0 if raw_pred <= 1.0 else raw_pred))
            except Exception:
                scoring_mode = "TRANSPARENT_RULE_BASED (XGBoost fallback)"
                final_score = sum(c.contribution for c in contributions)
        else:
            scoring_mode = "TRANSPARENT_RULE_BASED (XGBoost weights unavailable)"
            final_score = sum(c.contribution for c in contributions)

        final_score = max(0.0, min(100.0, final_score))

        # Confidence assessment based on data completeness
        track_comp = metrics.get("track_completeness", 1.0)
        confidence = round(0.70 * track_comp + 0.30 * (1.0 if has_temporal_overlap else 0.5), 3)

        # Build narrative explanation
        top_factors = sorted(contributions, key=lambda c: c.contribution, reverse=True)[:3]
        top_summary = "; ".join([f"{f.factor} ({f.contribution:.1f} pts: {f.explanation})" for f in top_factors])
        narrative_explanation = (
            f"Physical Consistency Score: {final_score:.1f}/100. "
            f"This candidate exhibits a consistent physical alignment with the backward hindcast scenario. "
            f"Key driving factors: {top_summary}."
        )

        limitations = [
            PHYSICAL_CONSISTENCY_DISCLAIMER,
            "Environmental forcing vectors are subject to spatio-temporal resolution limits (ERA5 wind and CMEMS currents).",
            "AIS reception gaps represent observation anomalies and do not establish intentional transponder deactivation.",
            f"Scoring computed via {scoring_mode}.",
        ]

        return PhysicalConsistencyResult(
            score=final_score,
            investigation_consistency_score=final_score,
            confidence=confidence,
            scoring_mode=scoring_mode,
            feature_values=feature_values,
            feature_contributions=[c.to_dict() for c in contributions],
            explanation=narrative_explanation,
            limitations=limitations,
            disclaimer=PHYSICAL_CONSISTENCY_DISCLAIMER,
        )


def rank_candidates(
    candidates_data: List[Dict[str, Any]],
    hindcast_origin_geometry: Optional[Union[BaseGeometry, Dict[str, Any]]],
    hindcast_origin_centroid: Optional[Tuple[float, float]],
    hindcast_time_window: Tuple[datetime, datetime],
    spill_detection_location: Optional[Tuple[float, float]] = None,
    spill_detection_time: Optional[datetime] = None,
    weights_dir: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    Ranks candidates by Physical Consistency Score only after all relevant evidence
    has been completely evaluated.

    Returns ranked list of candidate dicts with attached consistency results and 1-based ranks.
    """
    scorer = PhysicalConsistencyScorer(weights_dir=weights_dir)

    # First calculate Isolation Forest anomaly scores across the whole population
    feature_dicts = []
    for c in candidates_data:
        positions = c.get("positions_raw") or c.get("ais_track_raw") or []
        m = calculate_trajectory_metrics(positions, origin_geometry=hindcast_origin_geometry)
        feature_dicts.append(m)

    iforest = ExplainableIsolationForest()
    iforest_scores = iforest.fit_predict_scores(feature_dicts)

    evaluated_candidates = []
    for i, c in enumerate(candidates_data):
        positions = c.get("positions_raw") or c.get("ais_track_raw") or []
        iso_score = iforest_scores[i]["isolation_forest_score"] if i < len(iforest_scores) else 0.5
        cf_res = c.get("counterfactual_result")

        consistency_result = scorer.evaluate_candidate(
            candidate_positions=positions,
            hindcast_origin_geometry=hindcast_origin_geometry,
            hindcast_origin_centroid=hindcast_origin_centroid,
            hindcast_time_window=hindcast_time_window,
            spill_detection_location=spill_detection_location,
            spill_detection_time=spill_detection_time,
            vessel_type=c.get("vessel_type"),
            counterfactual_result=cf_res,
            isolation_forest_score=iso_score,
        )

        cand_output = dict(c)
        cand_output["physical_score"] = consistency_result.score
        cand_output["physical_consistency_score"] = consistency_result.score
        cand_output["investigation_consistency_score"] = consistency_result.investigation_consistency_score
        cand_output["confidence"] = consistency_result.confidence
        cand_output["consistency_scoring_mode"] = consistency_result.scoring_mode
        cand_output["feature_values"] = consistency_result.feature_values
        cand_output["feature_contributions"] = consistency_result.feature_contributions
        cand_output["consistency_explanation"] = consistency_result.explanation
        cand_output["limitations"] = consistency_result.limitations
        cand_output["disclaimer"] = consistency_result.disclaimer

        evaluated_candidates.append(cand_output)

    # Sort strictly by Physical Consistency Score descending
    evaluated_candidates.sort(key=lambda x: x["physical_score"], reverse=True)
    for rank_idx, c in enumerate(evaluated_candidates, start=1):
        c["rank"] = rank_idx

    return evaluated_candidates
