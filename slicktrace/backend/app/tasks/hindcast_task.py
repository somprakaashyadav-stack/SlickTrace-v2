"""
SlickTrace v2 — Hindcast Celery Task

Runs OpenDrift/OpenOil backward Lagrangian simulation,
stores trajectory GeoJSON and origin uncertainty in DB.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from celery import Task
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.hindcast import HindcastStatus


def _get_sync_session() -> Session:
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(
    bind=True,
    name="app.tasks.hindcast_task.run_hindcast_task",
    max_retries=1,
    default_retry_delay=60,
    queue="ocean",
)
def run_hindcast_task(self: Task, hindcast_run_id: str) -> dict:
    """Run backward Lagrangian hindcast simulation for the given run ID."""
    from app.models.hindcast import HindcastRun

    session = _get_sync_session()
    run = None

    try:
        run = session.get(HindcastRun, hindcast_run_id)
        if not run:
            logger.error(f"[HINDCAST] Run {hindcast_run_id} not found")
            return

        run.status = HindcastStatus.RUNNING
        session.commit()

        # Import and run hindcast
        from ocean.hindcast.runner import run_hindcast, InsufficientEnvironmentalData
        from ocean.hindcast.config import HindcastSimulationConfig, OilParameters
        from ocean.forcing.providers import WindProvider, CurrentProvider, WaveProvider
        from ocean.forcing.models import AOI
        from ocean.readers.base import OceanDataUnavailable

        # Retrieve simulation config from run
        cfg_dict = run.simulation_config or {}
        durations = cfg_dict.get("durations_hours", [4, 8, 12, run.hours_back or 24])
        n_particles = cfg_dict.get("n_particles", run.n_particles or 1000)
        oil_type = cfg_dict.get("oil_type", "GENERIC BUNKER C")
        allow_fallback = cfg_dict.get("allow_fallback", False)
        slick_poly = cfg_dict.get("slick_polygon")

        config = HindcastSimulationConfig(
            durations_hours=durations,
            n_particles=n_particles,
            oil_params=OilParameters(oil_type=oil_type),
        )

        max_h = max(durations)
        start_time = (run.detection_time - timedelta(hours=max_h + 2)).isoformat()
        end_time = (run.detection_time + timedelta(hours=1)).isoformat()
        pad = max(1.5, max_h * 0.05)
        aoi = AOI(
            lon_min=run.start_lon - pad,
            lat_min=run.start_lat - pad,
            lon_max=run.start_lon + pad,
            lat_max=run.start_lat + pad,
        )

        # 1. Fetch real wind forcing
        wp = WindProvider()
        wind_data = None
        try:
            wind_data = wp.get_wind(aoi=aoi, start=start_time, end=end_time)
        except OceanDataUnavailable as e:
            logger.warning(f"[HINDCAST] Wind forcing unavailable: {e}")
            raise InsufficientEnvironmentalData(f"insufficient environmental data: {e.reason}")

        # 2. Fetch real current forcing
        cp = CurrentProvider()
        current_data = None
        try:
            current_data = cp.get_currents(aoi=aoi, start=start_time, end=end_time, allow_fallback=allow_fallback)
        except OceanDataUnavailable as e:
            logger.warning(f"[HINDCAST] Ocean current forcing unavailable: {e}")
            raise InsufficientEnvironmentalData(f"insufficient environmental data: {e.reason}")

        # 3. Optional wave forcing
        wavp = WaveProvider()
        wave_data = None
        try:
            wave_data = wavp.get_waves(aoi=aoi, start=start_time, end=end_time)
        except Exception:
            pass

        # 4. Run OpenOil physical simulation
        result = run_hindcast(
            detection_time=run.detection_time,
            wind_forcing=wind_data,
            current_forcing=current_data,
            slick_polygon=slick_poly,
            wave_forcing=wave_data,
            start_lat=run.start_lat,
            start_lon=run.start_lon,
            config=config,
        )

        # Store results
        from geoalchemy2.shape import from_shape
        from shapely.geometry import shape, Point

        run.status = HindcastStatus.DONE
        run.origin_time_start = result.origin_time_start
        run.origin_time_end = result.origin_time_end
        run.wind_reader = result.wind_source
        run.current_reader = result.current_source
        run.trajectory_geojson = result.trajectory_geojson
        run.particle_timesteps_geojson = result.particle_timesteps_geojson
        run.uncertainty_metadata = result.uncertainty_metadata
        run.duration_slices = result.duration_slices
        run.simulation_config = result.simulation_config
        run.forcing_provenance = result.forcing_provenance

        run.origin_centroid = from_shape(
            Point(result.origin_lon, result.origin_lat), srid=4326
        )

        # Store P50, P75, P90 polygons if available
        p50 = result.uncertainty_metadata.get("p50_polygon")
        if p50:
            try:
                run.origin_p50_polygon = from_shape(shape(p50), srid=4326)
            except Exception:
                pass

        p75 = result.uncertainty_metadata.get("p75_polygon")
        if p75:
            try:
                run.origin_p75_polygon = from_shape(shape(p75), srid=4326)
            except Exception:
                pass

        p90 = result.uncertainty_metadata.get("p90_polygon")
        if p90:
            try:
                run.origin_p90_polygon = from_shape(shape(p90), srid=4326)
            except Exception:
                pass

        run.completed_at = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            f"[HINDCAST] Done: run_id={hindcast_run_id} "
            f"origin={result.origin_lat:.4f},{result.origin_lon:.4f}"
        )
        return {"status": "done", "run_id": hindcast_run_id}

    except Exception as exc:
        logger.exception(f"[HINDCAST] Failed: {exc}")
        if run:
            run.status = HindcastStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()
