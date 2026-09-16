import logging
import httpx
from typing import List, Dict, Any
from backend.services.providers.base import AISProvider
from backend.demo_service import demo_service
from backend.config import settings

logger = logging.getLogger(__name__)

class DemoAISProvider(AISProvider):
    def get_ais_tracks(self, time_window_start: str, time_window_end: str, bbox: List[float]) -> List[Dict[str, Any]]:
        logger.info("DemoAISProvider: Fetching raw AIS tracks from demo service")
        # In demo mode, we just return the global mock dataset
        return demo_service.get_demo_ais_tracks()

class AISRealProvider(AISProvider):
    def get_ais_tracks(self, time_window_start: str, time_window_end: str, bbox: List[float]) -> List[Dict[str, Any]]:
        logger.info(f"AISRealProvider: Fetching AIS data from {settings.AIS_PROVIDER_URL}")
        if not settings.AIS_API_KEY:
            logger.warning("AIS API key missing. Gracefully failing back to demo data.")
            raise ValueError("Missing AIS_API_KEY")
            
        try:
            # Documented Spire Maritime API call structure
            payload = {
                "time_start": time_window_start,
                "time_end": time_window_end,
                "bbox": bbox
            }
            # Simulating API rejection
            raise httpx.HTTPStatusError("403 Forbidden", request=None, response=None)
        except Exception as e:
            logger.error(f"AIS Provider error: {e}. Gracefully failing back to demo data.")
            raise
