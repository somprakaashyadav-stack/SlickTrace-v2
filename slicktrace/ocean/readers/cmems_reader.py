"""
SlickTrace v2 — Copernicus Marine Service (CMEMS) Ocean Current Reader

Fetches surface ocean currents (U/V) from CMEMS for OpenDrift forcing.
UNAVAILABLE if CMEMS_USERNAME/CMEMS_PASSWORD not configured.

Registration: https://marine.copernicus.eu/
"""
from __future__ import annotations

import os
from pathlib import Path

from ocean.readers.base import OceanDataUnavailable, OceanReader


class CMEMSReader(OceanReader):
    source_name = "Copernicus Marine (CMEMS)"
    requires_credentials = True

    # Global Ocean Physics Analysis and Forecast (1/12°, daily)
    DATASET_ID = "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"

    def __init__(self):
        self._username = os.environ.get("CMEMS_USERNAME", "").strip()
        self._password = os.environ.get("CMEMS_PASSWORD", "").strip()

    def check_availability(self) -> tuple[bool, str]:
        if not self._username or not self._password:
            return False, (
                "CMEMS_USERNAME and CMEMS_PASSWORD not configured. "
                "Register at https://marine.copernicus.eu/"
            )
        try:
            import copernicusmarine  # noqa: F401
            return True, "ok"
        except ImportError:
            return False, "copernicusmarine package not installed. pip install copernicusmarine"

    def _require_available(self) -> None:
        ok, reason = self.check_availability()
        if not ok:
            raise OceanDataUnavailable(
                source=self.source_name,
                reason=reason,
                registration_url="https://marine.copernicus.eu/",
            )

    def fetch_currents(
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
        Download CMEMS surface current U/V components for the given region and time.
        Returns path to downloaded NetCDF file.
        """
        self._require_available()
        import copernicusmarine

        copernicusmarine.subset(
            dataset_id=self.DATASET_ID,
            variables=["uo", "vo"],
            minimum_longitude=lon_min,
            maximum_longitude=lon_max,
            minimum_latitude=lat_min,
            maximum_latitude=lat_max,
            start_datetime=time_start,
            end_datetime=time_end,
            minimum_depth=0.0,
            maximum_depth=0.5,
            output_filename=str(output_path),
            username=self._username,
            password=self._password,
            force_download=True,
        )
        return output_path

    def fetch_wind(self, *args, **kwargs) -> Path:
        raise OceanDataUnavailable(
            source=self.source_name,
            reason="CMEMS does not provide wind fields. Use ERA5 for wind.",
        )
