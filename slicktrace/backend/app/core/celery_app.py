"""
SlickTrace v2 — Celery application factory.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "slicktrace",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.segmentation_task",
        "app.tasks.hindcast_task",
        "app.tasks.ais_query_task",
        "app.tasks.scoring_task",
        "app.tasks.dossier_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.segmentation_task.*": {"queue": "ml"},
        "app.tasks.hindcast_task.*": {"queue": "ocean"},
        "app.tasks.ais_query_task.*": {"queue": "ais"},
        "app.tasks.scoring_task.*": {"queue": "scoring"},
        "app.tasks.dossier_task.*": {"queue": "reporting"},
    },
)
