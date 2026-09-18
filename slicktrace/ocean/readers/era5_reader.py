"""
SlickTrace v2 — ERA5 Wind Field Reader (Copernicus CDS API)

Fetches ERA5 10m U/V wind components via cdsapi for OpenDrift forcing.
UNAVAILABLE if CDS_KEY environment variable not set.

Registration: https://cds.climate.copernicus.eu/
"""
from __future__ import annotations

import os
from pathlib import Path

from ocean.readers.base import OceanDataUnavailable, OceanReader


class ERA5Reader(OceanReader):
    source_name = "ERA5 (Copernicus CDS)"
    requires_credentials = True

    def __init__(self):
        self._cds_key = os.environ.get("CDS_KEY", "").strip()
        self._cds_url = os.environ.get("CDS_URL", "https://cds.climate.copernicus.eu/api/v2")

    def check_availability(self) -> tuple[bool, str]:
        if not self._cds_key:
            return False, "CDS_KEY not configured. Register at https://cds.climate.copernicus.eu/"
        try:
            import cdsapi  # noqa: F401
            return True, "ok"
        except ImportError:
            return False, "cdsapi package not installed. pip install cdsapi"

    def _require_available(self) -> None:
        ok, reason = self.check_availability()
        if not ok:
            raise OceanDataUnavailable(
                source=self.source_name,
                reason=reason,
                registration_url="https://cds.climate.copernicus.eu/",
            )

    def fetch_wind(
        self,
        lon_min: float,
        lat_min: float,
        lon_max: float,
        lat_max: float,
        time_start: str,
        time_end: str,
        output_path: Path,
    ) -> Path:
        """
        Download ERA5 10m U/V wind components for the given bounding box and time range.
        Returns path to downloaded NetCDF file.
        """
        self._require_available()
        import cdsapi
        from datetime import datetime

        t_start = datetime.fromisoformat(time_start)
        t_end = datetime.fromisoformat(time_end)

        # Build hours list for the request
        hours = sorted(set([
            f"{h:02d}:00" for h in range(t_start.hour, min(t_end.hour + 1, 24))
        ]))
        if not hours:
            hours = [f"{h:02d}:00" for h in range(24)]

        c = cdsapi.Client(url=self._cds_url, key=self._cds_key, quiet=True)
        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"],
                "year": [str(t_start.year)],
                "month": [f"{t_start.month:02d}"],
                "day": [f"{t_start.day:02d}", f"{t_end.day:02d}"],
                "time": hours,
                "area": [lat_max, lon_min, lat_min, lon_max],  # N, W, S, E
                "format": "netcdf",
            },
            str(output_path),
        )
        return output_path

    def fetch_currents(self, *args, **kwargs) -> Path:
        raise OceanDataUnavailable(
            source=self.source_name,
            reason="ERA5 does not provide ocean currents. Use CMEMS or HYCOM.",
        )
