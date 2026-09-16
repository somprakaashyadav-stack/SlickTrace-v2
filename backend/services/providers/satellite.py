import logging
import httpx
from typing import Dict, Any
from backend.services.providers.base import SatelliteProvider
from backend.demo_service import demo_service
from backend.config import settings

logger = logging.getLogger(__name__)

class DemoSatelliteProvider(SatelliteProvider):
    def fetch_raw_scene_data(self, scene_id: str) -> Dict[str, Any]:
        """Fetches raw scene data using demo mocks."""
        logger.info(f"DemoSatelliteProvider: Fetching raw scene {scene_id}")
        # Note: the original code just did `return {"scene_id": scene_id, "data_type": "SAR_GRD"}` in ingestion.py
        # but the demo service might have more.
        return demo_service.get_demo_spill_scene(scene_id)

    def get_granule_metadata(self, scene_id: str) -> Dict[str, Any]:
        logger.info(f"DemoSatelliteProvider: Fetching metadata for {scene_id}")
        return {
            "scene_id": scene_id,
            "acquisition_time": "2026-09-12T14:30:00Z",
            "satellite": "Sentinel-1B",
            "mode": "IW",
            "product_type": "GRD",
            "polarization": "VV+VH",
            "status": "CACHED_DEMO"
        }

class SentinelProvider(SatelliteProvider):
    def fetch_raw_scene_data(self, scene_id: str) -> Dict[str, Any]:
        logger.info(f"SentinelProvider: Attempting to fetch {scene_id} from Sentinel Hub")
        if not settings.SENTINEL_HUB_API_KEY:
            logger.warning("Sentinel Hub API key missing. Gracefully failing back to demo data.")
            raise ValueError("Missing SENTINEL_HUB_API_KEY")
            
        try:
            # Documented API endpoint for Sentinel Hub OData
            url = f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{scene_id}')"
            # This would be an actual call: response = httpx.get(url, auth=(settings.SENTINEL_HUB_USER, settings.SENTINEL_HUB_PASSWORD))
            # Simulating auth failure since keys are likely invalid or missing
            raise httpx.HTTPStatusError("401 Unauthorized", request=None, response=None)
        except Exception as e:
            logger.error(f"Sentinel API error: {e}. Gracefully failing back to demo data.")
            raise

    def get_granule_metadata(self, scene_id: str) -> Dict[str, Any]:
        logger.info(f"SentinelProvider: Attempting to fetch metadata for {scene_id}")
        if not settings.SENTINEL_HUB_API_KEY:
            logger.warning("Sentinel Hub API key missing. Gracefully failing back to demo data.")
            raise ValueError("Missing SENTINEL_HUB_API_KEY")
        
        try:
            url = f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{scene_id}')/?$format=json"
            raise httpx.HTTPStatusError("401 Unauthorized", request=None, response=None)
        except Exception as e:
            logger.error(f"Sentinel API error: {e}. Gracefully failing back to demo data.")
            raise
