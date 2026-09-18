"""
SlickTrace v2 — Global Fishing Watch (GFW) AIS Adapter

Queries the GFW Events API for vessel positions in a given time/area window.
UNAVAILABLE if GFW_API_TOKEN not configured.

Registration: https://globalfishingwatch.org/
API docs: https://globalfishingwatch.org/our-apis/
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

GFW_API_BASE = "https://gateway.api.globalfishingwatch.org/v3"


class GFWAdapterUnavailable(Exception):
    """Raised when GFW API token is not configured."""
    pass


class GFWAdapter:
    """
    Global Fishing Watch vessel position adapter.
    Queries the GFW Events API for vessels in a spatiotemporal window.
    """

    def __init__(self):
        self._token = os.environ.get("GFW_API_TOKEN", "").strip()

    def check_availability(self) -> tuple[bool, str]:
        if not self._token:
            return False, (
                "GFW_API_TOKEN not configured. "
                "Register at https://globalfishingwatch.org/ and set GFW_API_TOKEN"
            )
        return True, "ok"

    def _require_available(self) -> None:
        ok, reason = self.check_availability()
        if not ok:
            raise GFWAdapterUnavailable(f"[UNAVAILABLE] Global Fishing Watch: {reason}")

    def query_vessels_in_window(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        time_start: datetime,
        time_end: datetime,
        vessel_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query GFW for vessel positions within the given spatiotemporal window.

        Args:
            lat_min, lat_max, lon_min, lon_max: Bounding box (WGS84)
            time_start, time_end: UTC datetimes
            vessel_types: Optional filter (e.g. ["tanker", "cargo"])

        Returns:
            List of vessel dicts: {mmsi, vessel_name, vessel_type, positions: [...]}

        Raises:
            GFWAdapterUnavailable: if token not configured
        """
        self._require_available()

        try:
            import httpx
        except ImportError:
            raise GFWAdapterUnavailable("httpx not installed. pip install httpx")

        headers = {"Authorization": f"Bearer {self._token}"}
        params = {
            "datasets[0]": "public-global-fishing-events:latest",
            "startDate": time_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDate": time_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "geometry": (
                f'{{"type":"Polygon","coordinates":[[['
                f'[{lon_min},{lat_min}],[{lon_max},{lat_min}],'
                f'[{lon_max},{lat_max}],[{lon_min},{lat_max}],'
                f'[{lon_min},{lat_min}]]]]}}'
            ),
            "limit": 200,
            "offset": 0,
        }

        response = httpx.get(
            f"{GFW_API_BASE}/events",
            headers=headers,
            params=params,
            timeout=30,
        )

        if response.status_code == 401:
            raise GFWAdapterUnavailable("GFW API token invalid or expired.")
        if response.status_code != 200:
            raise GFWAdapterUnavailable(
                f"GFW API returned HTTP {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        vessels = []
        for event in data.get("entries", []):
            vessel = event.get("vessel", {})
            vessels.append({
                "mmsi": vessel.get("mmsi"),
                "vessel_name": vessel.get("name"),
                "vessel_type": vessel.get("type"),
                "flag": vessel.get("flag"),
                "event_type": event.get("type"),
                "event_start": event.get("start"),
                "event_end": event.get("end"),
                "latitude": event.get("position", {}).get("lat"),
                "longitude": event.get("position", {}).get("lon"),
                "provider": "global_fishing_watch",
                "dataset": "public-global-fishing-events:latest",
            })

        logger.info(f"[GFW] Found {len(vessels)} vessel events in window")
        return vessels
