"""
SlickTrace v2 — Physical Consistency Scoring Celery Task

Evaluates and ranks candidate vessels using the Physical Consistency Ranking Engine.
Computes 10 physical consistency factors:
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

Strict Terminology Notice:
Primary Name: "Physical Consistency Score"
Secondary Name: "Investigation Consistency Score"
Never label or describe as a guilt score.

Mandatory UI / Report Notice:
"This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility."
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from celery import Task
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.celery_app import celery_app
from app.core.config import settings
from ais.ranking_engine import PhysicalConsistencyScorer, rank_candidates


def _get_sync_session() -> Session:
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(
    bind=True,
    name="app.tasks.scoring_task.run_scoring",
    max_retries=1,
    queue="scoring",
)
def run_scoring(self: Task, incident_id: str, ais_query_id: str) -> dict:
    """Score and rank candidate vessels by Physical Consistency Score."""
    from app.models.candidate import CandidateVessel
    from app.models.ais_query import AISQuery
    from app.models.hindcast import HindcastRun
    from geoalchemy2.shape import to_shape

    session = _get_sync_session()

    try:
        query_record = session.get(AISQuery, ais_query_id)
        if not query_record:
            logger.error(f"[SCORING] AISQuery record {ais_query_id} not found")
            return {"status": "error", "message": "AISQuery not found"}

        # Fetch hindcast run and origin geometry
        hindcast = session.get(HindcastRun, str(query_record.hindcast_run_id))
        origin_poly = None
        origin_lat = None
        origin_lon = None

        if hindcast:
            if hindcast.origin_p50_polygon:
                origin_poly = to_shape(hindcast.origin_p50_polygon)
            elif hindcast.origin_p75_polygon:
                origin_poly = to_shape(hindcast.origin_p75_polygon)
            elif hindcast.origin_p90_polygon:
                origin_poly = to_shape(hindcast.origin_p90_polygon)

            if hindcast.origin_centroid:
                pt = to_shape(hindcast.origin_centroid)
                origin_lat, origin_lon = pt.y, pt.x

            time_window = (
                hindcast.origin_time_start or query_record.time_start,
                hindcast.origin_time_end or query_record.time_end,
            )
            spill_loc = (hindcast.start_lat, hindcast.start_lon) if hindcast.start_lat and hindcast.start_lon else None
            spill_time = hindcast.detection_time
        else:
            time_window = (query_record.time_start, query_record.time_end)
            spill_loc = None
            spill_time = None

        origin_centroid_tuple = (origin_lat, origin_lon) if (origin_lat is not None and origin_lon is not None) else None

        # Get all candidates for this query
        candidates = (
            session.query(CandidateVessel)
            .filter(CandidateVessel.ais_query_id == ais_query_id)
            .all()
        )

        if not candidates:
            logger.info(f"[SCORING] No candidates found for query {ais_query_id}")
            return {"status": "done", "candidates_ranked": 0}

        scorer = PhysicalConsistencyScorer(weights_dir=settings.ML_WEIGHTS_DIR)

        candidate_evaluations: List[Tuple[CandidateVessel, Any]] = []

        for c in candidates:
            positions = c.ais_track_raw if isinstance(c.ais_track_raw, list) else []
            # Counterfactual status if present
            cf_info = {
                "counterfactual_consistent": c.counterfactual_consistent,
                "counterfactual_run": c.counterfactual_run,
            } if c.counterfactual_run else None

            res = scorer.evaluate_candidate(
                candidate_positions=positions,
                hindcast_origin_geometry=origin_poly,
                hindcast_origin_centroid=origin_centroid_tuple,
                hindcast_time_window=time_window,
                spill_detection_location=spill_loc,
                spill_detection_time=spill_time,
                vessel_type=c.vessel_type,
                counterfactual_result=cf_info,
                isolation_forest_score=c.isolation_forest_score,
            )

            candidate_evaluations.append((c, res))

        # Sort strictly by Physical Consistency Score descending ONLY after all evidence calculated
        candidate_evaluations.sort(key=lambda item: item[1].score, reverse=True)

        for rank_num, (c, res) in enumerate(candidate_evaluations, start=1):
            c.rank = rank_num
            c.physical_score = res.score
            c.physical_consistency_score = res.score
            c.investigation_consistency_score = res.investigation_consistency_score
            c.confidence = res.confidence
            c.scoring_mode = res.scoring_mode

            # Factors
            fvals = res.feature_values
            c.spatial_consistency = fvals.get("spatial_consistency")
            c.temporal_consistency = fvals.get("temporal_consistency")
            c.origin_proximity = fvals.get("origin_proximity")
            c.drift_consistency = fvals.get("drift_consistency")
            c.trajectory_consistency = fvals.get("trajectory_consistency")
            c.speed_behavior_consistency = fvals.get("speed_behavior_consistency")
            c.course_behavior_consistency = fvals.get("course_behavior_consistency")
            c.ais_continuity_score = fvals.get("AIS_continuity")
            c.counterfactual_similarity = fvals.get("counterfactual_similarity")

            # Legacy fields compatibility
            c.proximity_score = fvals.get("origin_proximity")
            c.timing_score = fvals.get("temporal_consistency")
            c.heading_score = fvals.get("drift_consistency")
            c.speed_anomaly_score = fvals.get("speed_behavior_consistency")
            c.ais_gap_score = fvals.get("AIS_continuity")

            # Explainability & Disclaimers
            c.feature_values = fvals
            c.feature_contributions = res.feature_contributions
            c.consistency_explanation = res.explanation
            c.limitations = res.limitations
            c.disclaimer = res.disclaimer

        session.commit()
        logger.info(
            f"[SCORING] Successfully calculated Physical Consistency Scores and ranked {len(candidates)} candidates for incident {incident_id}"
        )
        return {
            "status": "done",
            "candidates_ranked": len(candidates),
            "scoring_mode": candidate_evaluations[0][1].scoring_mode if candidate_evaluations else "NONE",
        }

    except Exception as exc:
        logger.exception(f"[SCORING] Failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="app.tasks.scoring_task.run_counterfactual_task",
    max_retries=1,
    queue="scoring",
)
def run_counterfactual_task(self: Task, candidate_id: str) -> dict:
    """
    Run forward Lagrangian counterfactual verification for a candidate vessel:
    1. Retrieves candidate AIS track near release window.
    2. Explores hypothetical release points across multiple time offsets.
    3. Runs forward advection under historical environmental forcing to satellite detection time.
    4. Compares predicted slick against observed satellite slick geometry.
    5. Calculates centroid error, shape overlap, IoU, and physics consistency.
    """
    from app.models.candidate import CandidateVessel
    from app.models.ais_query import AISQuery
    from app.models.hindcast import HindcastRun
    from app.models.detection import SpillDetection
    from geoalchemy2.shape import to_shape
    from ocean.hindcast.counterfactual import (
        run_counterfactual_verification,
        InsufficientCounterfactualData,
    )
    from ocean.forcing.providers import ERA5WindProvider, CopernicusCurrentProvider, AOI

    session = _get_sync_session()

    try:
        candidate = session.get(CandidateVessel, candidate_id)
        if not candidate:
            return {"status": "error", "message": "Candidate not found"}

        query_record = session.get(AISQuery, str(candidate.ais_query_id)) if candidate.ais_query_id else None
        hindcast = session.get(HindcastRun, str(query_record.hindcast_run_id)) if query_record else None
        detection = session.get(SpillDetection, str(hindcast.detection_id)) if hindcast else None

        candidate.counterfactual_run = True

        # Check for required data
        positions = candidate.ais_track_raw if isinstance(candidate.ais_track_raw, list) else []
        if not positions or not hindcast:
            candidate.counterfactual_consistent = None
            candidate.counterfactual_notes = "insufficient data: missing candidate AIS positions or hindcast metadata"
            session.commit()
            return {"status": "insufficient data", "message": candidate.counterfactual_notes}

        # Determine observed slick geometry
        obs_poly_geojson = None
        if detection and detection.polygon_geojson:
            obs_poly_geojson = detection.polygon_geojson
        elif hindcast.start_lat and hindcast.start_lon:
            # Fallback box around detected point
            p_lat, p_lon = hindcast.start_lat, hindcast.start_lon
            obs_poly_geojson = {
                "type": "Polygon",
                "coordinates": [[[p_lon - 0.02, p_lat - 0.02], [p_lon + 0.02, p_lat - 0.02], [p_lon + 0.02, p_lat + 0.02], [p_lon - 0.02, p_lat + 0.02], [p_lon - 0.02, p_lat - 0.02]]],
            }

        detection_time = hindcast.detection_time
        time_window = (
            hindcast.origin_time_start or query_record.time_start,
            hindcast.origin_time_end or query_record.time_end,
        )

        # Retrieve environmental forcing
        wind_forcing = None
        current_forcing = None

        try:
            # Bounding AOI for simulation
            c_lats = [float(p.get("latitude", p.get("lat", 0))) for p in positions if p.get("latitude") or p.get("lat")]
            c_lons = [float(p.get("longitude", p.get("lon", 0))) for p in positions if p.get("longitude") or p.get("lon")]
            if c_lats and c_lons:
                all_lats = c_lats + [hindcast.start_lat]
                all_lons = c_lons + [hindcast.start_lon]
                aoi = AOI(min(all_lons) - 0.5, min(all_lats) - 0.5, max(all_lons) + 0.5, max(all_lats) + 0.5)
                wind_prov = ERA5WindProvider()
                curr_prov = CopernicusCurrentProvider()
                wind_forcing = wind_prov.get_wind(aoi, time_window[0] - timedelta(hours=6), detection_time + timedelta(hours=2))
                current_forcing = curr_prov.get_currents(aoi, time_window[0] - timedelta(hours=6), detection_time + timedelta(hours=2))
        except Exception as e:
            logger.warning(f"[COUNTERFACTUAL] Forcing provider retrieval note: {e}")

        # Execute counterfactual verification engine
        try:
            cf_res = run_counterfactual_verification(
                candidate_positions=positions,
                observed_slick_geometry=obs_poly_geojson,
                spill_detection_time=detection_time,
                candidate_release_window=time_window,
                wind_forcing=wind_forcing,
                current_forcing=current_forcing,
            )

            candidate.counterfactual_consistent = cf_res.counterfactual_consistent
            candidate.counterfactual_similarity = cf_res.best_metrics.iou
            candidate.counterfactual_notes = (
                f"Forward Lagrangian verification {cf_res.status}: centroid error {cf_res.best_metrics.centroid_error_km:.2f} km, "
                f"IoU {cf_res.best_metrics.iou*100:.1f}%, physics consistency {cf_res.best_metrics.physics_consistency:.1f}/100."
            )
            candidate.counterfactual_results = cf_res.to_dict()
            candidate.counterfactual_layers = {
                "observed_slick_layer": cf_res.observed_slick_layer,
                "simulated_slick_layer": cf_res.simulated_slick_layer,
                "overlap_layer": cf_res.overlap_layer,
            }
        except InsufficientCounterfactualData as e:
            candidate.counterfactual_consistent = None
            candidate.counterfactual_similarity = None
            candidate.counterfactual_notes = f"insufficient data: {e}"
            candidate.counterfactual_results = {"status": "insufficient data", "message": str(e)}

        session.commit()

        # Re-trigger physical consistency scoring update for the incident
        if query_record:
            run_scoring(str(query_record.incident_id), str(query_record.id))

        return {
            "status": "done" if candidate.counterfactual_consistent is not None else "insufficient data",
            "candidate_id": candidate_id,
            "consistent": candidate.counterfactual_consistent,
            "notes": candidate.counterfactual_notes,
        }

    except Exception as exc:
        logger.exception(f"[COUNTERFACTUAL] Failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()

