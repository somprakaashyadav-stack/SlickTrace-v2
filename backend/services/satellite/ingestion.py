import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("slicktrace.satellite.ingestion")
SAMPLE_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample" / "sample_sar_scene.json"

class SatelliteIngestionService:
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode

    def get_granule_metadata(self, scene_id: str) -> Dict[str, Any]:
        """Returns granule parameters and sensor specifications."""
        return {
            "scene_id": scene_id,
            "satellite": "Sentinel-1B",
            "sensor": "C-Band SAR (IW)",
            "acquisition_time": "2026-09-12T14:30:00Z",
            "polarization": "VV",
            "resolution_m": 10.0,
            "orbit_direction": "DESCENDING",
            "incidence_angle_range_deg": [34.2, 38.6],
            "copernicus_data_space_link": f"https://dataspace.copernicus.eu/odata/v1/Products('{scene_id}')"
        }

    def fetch_raw_scene_data(self, scene_id: str) -> Dict[str, Any]:
        """
        In DEMO MODE, loads synthetic Sentinel-1 SAR intensity matrix from sample cache.
        In Production mode, authenticates with Copernicus OData API or Sentinel Hub API.
        """
        if self.demo_mode:
            if SAMPLE_FILE.exists():
                with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
                    logger.info(f"DEMO MODE: Ingested SAR scene from {SAMPLE_FILE.name}")
                    return json.load(f)
            else:
                logger.warning(f"Sample file {SAMPLE_FILE} not found. Generating fallback array.")
                return {
                    "scene_id": scene_id,
                    "satellite": "Sentinel-1B",
                    "sensor": "C-Band SAR (IW)",
                    "acquisition_time": "2026-09-12T14:30:00Z",
                    "polarization": "VV",
                    "resolution_m": 10.0,
                    "dimensions": [64, 64],
                    "raw_intensity_matrix": [[0.15 for _ in range(64)] for _ in range(64)]
                }
        else:
            # Production Copernicus OData API Integration Point
            raise NotImplementedError("Real Sentinel API fetch requires COPERNICUS_USER & COPERNICUS_PASSWORD in .env")

ingestion_service = SatelliteIngestionService()
