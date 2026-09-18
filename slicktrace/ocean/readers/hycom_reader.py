"""
SlickTrace v2 — HYCOM THREDDS Ocean Current Reader

Public fallback for ocean currents when CMEMS is unavailable.
No credentials required. Uses HYCOM GLBv0.08 via THREDDS OPeNDAP.

Note: HYCOM THREDDS has occasional outages. Always check availability
before including in production runs.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from ocean.readers.base import OceanDataUnavailable, OceanReader

# HYCOM GLBv0.08 OPeNDAP base URL
HYCOM_THREDDS_BASE = "https://tds.hycom.org/thredds/dodsC/GLBy0.08/expt_93.0"


class HYCOMReader(OceanReader):
    source_name = "HYCOM (Public THREDDS)"
    requires_credentials = False

    def check_availability(self) -> tuple[bool, str]:
        try:
            import netCDF4  # noqa: F401
            return True, "ok (no credentials required)"
        except ImportError:
            return False, "netCDF4 not installed. pip install netCDF4"

    def _require_available(self) -> None:
        ok, reason = self.check_availability()
        if not ok:
            raise OceanDataUnavailable(
                source=self.source_name,
                reason=reason,
                registration_url="https://tds.hycom.org/",
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
        Download HYCOM surface currents (water_u, water_v) for given region/time.
        Saves as NetCDF to output_path.
        """
        self._require_available()
        try:
            import netCDF4
            import numpy as np

            url = f"{HYCOM_THREDDS_BASE}"
            ds = netCDF4.Dataset(url)

            # Get coordinate arrays
            lats = ds.variables["lat"][:]
            lons = ds.variables["lon"][:]
            times = netCDF4.num2date(
                ds.variables["time"][:],
                ds.variables["time"].units,
            )

            # Time indices
            t0 = datetime.fromisoformat(time_start)
            t1 = datetime.fromisoformat(time_end)
            time_idx = [
                i for i, t in enumerate(times)
                if t0 <= datetime(t.year, t.month, t.day, t.hour) <= t1
            ]
            if not time_idx:
                raise OceanDataUnavailable(
                    source=self.source_name,
                    reason=f"No HYCOM data found for time range {time_start} to {time_end}",
                )

            # Spatial indices
            lat_idx = np.where((lats >= lat_min) & (lats <= lat_max))[0]
            lon_idx = np.where((lons >= lon_min) & (lons <= lon_max))[0]

            u = ds.variables["water_u"][
                time_idx, 0, lat_idx[0]:lat_idx[-1]+1, lon_idx[0]:lon_idx[-1]+1
            ]
            v = ds.variables["water_v"][
                time_idx, 0, lat_idx[0]:lat_idx[-1]+1, lon_idx[0]:lon_idx[-1]+1
            ]

            # Write subset to NetCDF
            out = netCDF4.Dataset(str(output_path), "w")
            out.createDimension("time", len(time_idx))
            out.createDimension("lat", len(lat_idx))
            out.createDimension("lon", len(lon_idx))

            t_var = out.createVariable("time", "f8", ("time",))
            t_var.units = ds.variables["time"].units
            t_var[:] = ds.variables["time"][time_idx]

            la = out.createVariable("lat", "f4", ("lat",))
            la[:] = lats[lat_idx]
            lo = out.createVariable("lon", "f4", ("lon",))
            lo[:] = lons[lon_idx]

            u_var = out.createVariable("water_u", "f4", ("time", "lat", "lon"), fill_value=1e20)
            u_var.units = "m s-1"
            u_var[:] = u

            v_var = out.createVariable("water_v", "f4", ("time", "lat", "lon"), fill_value=1e20)
            v_var.units = "m s-1"
            v_var[:] = v

            out.close()
            ds.close()
            return output_path

        except OceanDataUnavailable:
            raise
        except Exception as e:
            raise OceanDataUnavailable(
                source=self.source_name,
                reason=f"HYCOM fetch failed: {e}. Server may be temporarily unavailable.",
                registration_url="https://tds.hycom.org/",
            )

    def fetch_wind(self, *args, **kwargs) -> Path:
        raise OceanDataUnavailable(
            source=self.source_name,
            reason="HYCOM does not provide wind fields. Use ERA5.",
        )
