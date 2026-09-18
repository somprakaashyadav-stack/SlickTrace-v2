"""
SlickTrace v2 — AIS Query Celery Task

Executes DuckDB Spatial spatiotemporal query, performs trajectory & behavioral analysis
on candidate tracks (calculating all kinematics, observation gaps, and Isolation Forest anomaly scores),
and creates transparent candidate records.
"""
from __future__ import annotations

from datetime import datetime, timezone

from celery import Task
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.celery_app import celery_app
from app.core.config import settings


def _get_sync_session() -> Session:
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(
    bind=True,
    name="app.tasks.ais_query_task.run_ais_query",
    max_retries=2,
    default_retry_delay=30,
    queue="ais",
)
def run_ais_query(self: Task, query_id: str) -> dict:
    """Execute DuckDB Spatial AIS query and create candidate vessel records with full trajectory analysis."""
    from app.models.ais_query import AISQuery
    from app.models.candidate import CandidateVessel
    from app.models.ais_position import AISPosition
    from geoalchemy2.shape import to_shape

    session = _get_sync_session()

    try:
        query_record = session.get(AISQuery, query_id)
        if not query_record:
            logger.error(f"[AIS QUERY] Record {query_id} not found")
            return {"status": "error", "message": f"Record {query_id} not found"}

        # Convert DB geometry to WKT/Shape
        search_geom = to_shape(query_record.search_polygon)

        # Generate transparent candidate set with complete kinematic & behavioral analysis
        from ais.candidate_generation import generate_transparent_candidates
        candidates_raw = generate_transparent_candidates(
            origin_geometry=search_geom,
            time_start=query_record.time_start,
            time_end=query_record.time_end,
            radius_km=query_record.radius_km or 10.0,
        )

        query_record.vessel_count = len(candidates_raw)
        query_record.results_summary = {
            "mmsis": [c.mmsi for c in candidates_raw],
            "source_counts": {},
        }
        session.commit()

        if not candidates_raw:
            logger.info(f"[AIS QUERY] No vessels found in window for query {query_id}")
            return {"status": "done", "vessels_found": 0}

        # Create CandidateVessel records with all calculated metrics & explainable anomalies
        for cand in candidates_raw:
            candidate_record = CandidateVessel(
                incident_id=query_record.incident_id,
                ais_query_id=query_record.id,
                mmsi=cand.mmsi,
                vessel_name=cand.vessel_name,
                vessel_type=cand.vessel_type,
                observations_count=cand.observations_count,
                first_observation=cand.first_observation,
                last_observation=cand.last_observation,
                minimum_distance_to_origin=cand.minimum_distance_to_origin,
                time_difference=cand.time_difference,
                strategies_matched=cand.strategies_matched,
                status_display=cand.status_display,
                # Trajectory & Behavior metrics
                mean_sog=cand.mean_sog,
                min_sog=cand.min_sog,
                max_sog=cand.max_sog,
                speed_change=cand.speed_change,
                acceleration=cand.acceleration,
                mean_cog=cand.mean_cog,
                course_change=cand.course_change,
                turn_rate=cand.turn_rate,
                time_in_origin_zone=cand.time_in_origin_zone,
                distance_to_origin=cand.distance_to_origin,
                ais_gap_count=cand.ais_gap_count,
                max_ais_gap_duration=cand.max_ais_gap_duration,
                track_completeness=cand.track_completeness,
                trajectory_length=cand.trajectory_length,
                behavioral_metrics=cand.trajectory_metrics,
                # Anomalies & Explainability
                anomalies=cand.named_anomalies,
                detailed_anomalies=cand.anomalies,
                isolation_forest_score=cand.isolation_forest_score,
                isolation_forest_explanations=cand.isolation_forest_explanations,
                ais_track_raw=cand.positions_raw if cand.positions_raw else cand.track_geometry,
            )
            session.add(candidate_record)

            # Persist positions into PostGIS
            for pos in cand.positions_raw:
                try:
                    ts_raw = pos.get("timestamp_utc") or pos.get("base_datetime")
                    if isinstance(ts_raw, str):
                        dt = datetime.fromisoformat(ts_raw)
                    elif isinstance(ts_raw, datetime):
                        dt = ts_raw
                    else:
                        continue

                    lat_v = pos.get("latitude") if "latitude" in pos else pos.get("lat")
                    lon_v = pos.get("longitude") if "longitude" in pos else pos.get("lon")
                    if lat_v is None or lon_v is None:
                        continue

                    wkt_point = f"POINT({lon_v} {lat_v})"
                    ais_pos = AISPosition(
                        mmsi=cand.mmsi,
                        vessel_name=cand.vessel_name,
                        vessel_type=cand.vessel_type,
                        timestamp_utc=dt,
                        latitude=float(lat_v),
                        longitude=float(lon_v),
                        sog=pos.get("sog"),
                        cog=pos.get("cog"),
                        heading=pos.get("heading"),
                        geom=wkt_point,
                        provider=pos.get("provider", "marinecadastre"),
                        dataset=pos.get("dataset", "bulk_ais"),
                    )
                    session.add(ais_pos)
                except Exception as e:
                    logger.warning(f"Skipping persistence of AIS position: {e}")

        session.commit()

        logger.info(
            f"[AIS QUERY] Done: {len(candidates_raw)} candidate vessels analyzed with full trajectory metrics."
        )
        return {"status": "done", "vessels_found": len(candidates_raw)}

    except Exception as exc:
        logger.exception(f"[AIS QUERY] Failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()
