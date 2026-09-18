"""
SlickTrace v2 — Core Configuration

Enforces REAL MODE / DEMO MODE contract:
- REAL MODE: all required credentials must be present; raises ValueError if missing.
- DEMO MODE: credentials optional; fixture data used with explicit banner.
No silent fallback from REAL to DEMO.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OperationMode(str, Enum):
    REAL = "real"
    DEMO = "demo"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Mode
    SLICKTRACE_MODE: OperationMode = OperationMode.REAL

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://slicktrace:changeme@localhost:5432/slicktrace"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET_IMAGERY: str = "slicktrace-imagery"
    MINIO_BUCKET_OUTPUTS: str = "slicktrace-outputs"
    MINIO_BUCKET_DOSSIERS: str = "slicktrace-dossiers"
    MINIO_USE_SSL: bool = False

    # Copernicus / Remote sensing
    CDSE_USERNAME: Optional[str] = None
    CDSE_PASSWORD: Optional[str] = None

    # Ocean physics
    CMEMS_USERNAME: Optional[str] = None
    CMEMS_PASSWORD: Optional[str] = None
    CDS_URL: Optional[str] = None
    CDS_KEY: Optional[str] = None

    # AIS
    GFW_API_TOKEN: Optional[str] = None

    # INCOIS (optional stub)
    INCOIS_API_URL: Optional[str] = None
    INCOIS_API_KEY: Optional[str] = None

    # ML Service
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_WEIGHTS_DIR: str = "/app/weights"

    # Security
    SECRET_KEY: str = "changeme_32byte_secret_key_here!!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def is_real_mode(self) -> bool:
        return self.SLICKTRACE_MODE == OperationMode.REAL

    @property
    def is_demo_mode(self) -> bool:
        return self.SLICKTRACE_MODE == OperationMode.DEMO

    def get_unavailable_sources(self) -> dict[str, str]:
        """
        Returns a dict of data source name -> reason for all sources
        that are currently unavailable (missing credentials).
        Used to expose UNAVAILABLE state in API responses and UI.
        """
        unavailable: dict[str, str] = {}

        if not self.CDSE_USERNAME or not self.CDSE_PASSWORD:
            unavailable["copernicus_dataspace"] = (
                "CDSE_USERNAME and CDSE_PASSWORD not configured. "
                "Register at https://dataspace.copernicus.eu/"
            )
        if not self.CMEMS_USERNAME or not self.CMEMS_PASSWORD:
            unavailable["copernicus_marine"] = (
                "CMEMS_USERNAME and CMEMS_PASSWORD not configured. "
                "Register at https://marine.copernicus.eu/"
            )
        if not self.CDS_KEY:
            unavailable["era5_cds"] = (
                "CDS_KEY not configured. "
                "Register at https://cds.climate.copernicus.eu/"
            )
        if not self.GFW_API_TOKEN:
            unavailable["global_fishing_watch"] = (
                "GFW_API_TOKEN not configured (optional). "
                "Register at https://globalfishingwatch.org/"
            )

        return unavailable


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
