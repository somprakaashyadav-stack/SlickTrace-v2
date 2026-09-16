from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SlickTrace v2"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # DEMO MODE configuration
    DEMO_MODE: bool = True
    DEMO_DATASET: str = "mumbai_offshore_2026"
    DRIFT_ENGINE: str = "demo"  # 'demo' or 'opendrift'
    
    # Provider configuration
    DATA_MODE: str = "demo" # 'demo' or 'real'
    
    # API Keys for real providers
    SENTINEL_HUB_API_KEY: Optional[str] = None
    AIS_API_KEY: Optional[str] = None
    AIS_PROVIDER_URL: str = "https://api.spire.com/ais" # Documenting Spire Maritime
    METOCEAN_API_KEY: Optional[str] = None
    METOCEAN_PROVIDER_URL: str = "https://marine-api.open-meteo.com/v1/marine"

    # Database configuration (Defaults to local SQLite fallback if PostGIS URL is unconfigured)
    DATABASE_URL: str = "sqlite:///./slicktrace.db"

    # Host & Cors
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "https://slick-tracev2.vercel.app"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
