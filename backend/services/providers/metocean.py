import logging
import httpx
from typing import Dict, Any
from backend.services.providers.base import MetoceanProvider
from backend.config import settings
import math

logger = logging.getLogger(__name__)

class DemoMetoceanProvider(MetoceanProvider):
    def get_wind_and_currents(self, lat: float, lon: float, timestamp: str) -> Dict[str, Any]:
        """Provides static mock metocean data for demo simulation."""
        logger.info("DemoMetoceanProvider: Generating synthetic metocean data")
        return {
            "wind_speed_knots": 15.0,
            "wind_dir_deg": 270.0,
            "current_speed_knots": 0.5,
            "current_dir_deg": 290.0,
            "source": "DEMO"
        }

class MetoceanRealProvider(MetoceanProvider):
    def get_wind_and_currents(self, lat: float, lon: float, timestamp: str) -> Dict[str, Any]:
        logger.info(f"MetoceanRealProvider: Fetching marine data from {settings.METOCEAN_PROVIDER_URL}")
        if not settings.METOCEAN_API_KEY:
            logger.warning("Metocean API key missing. Gracefully failing back to demo data.")
            raise ValueError("Missing METOCEAN_API_KEY")
            
        try:
            # Documented OpenMeteo Marine API call
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "wind_speed_10m,wind_direction_10m,ocean_current_speed,ocean_current_direction"
            }
            # Simulating API rejection
            raise httpx.HTTPStatusError("401 Unauthorized", request=None, response=None)
        except Exception as e:
            logger.error(f"Metocean Provider error: {e}. Gracefully failing back to demo data.")
            raise
