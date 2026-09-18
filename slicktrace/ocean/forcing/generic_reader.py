"""
SlickTrace v2 — Generic Gridded Environmental Forcing Reader

Normalizes NetCDF, GRIB, OPeNDAP, and Zarr gridded datasets into NormalizedForcingData
by detecting coordinate and meteorological/oceanographic vector variable conventions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ocean.forcing.models import ForcingProvenance, NormalizedForcingData


# Candidate variable names across common climate / ocean modeling formats
LAT_CANDIDATES = ["latitude", "lat", "nav_lat", "y", "lat_rho"]
LON_CANDIDATES = ["longitude", "lon", "nav_lon", "x", "lon_rho"]
TIME_CANDIDATES = ["time", "datetime", "date", "times", "valid_time"]

WIND_U_CANDIDATES = ["u10", "10m_u_component_of_wind", "wind_u", "u_wind", "u", "U10M", "u10m"]
WIND_V_CANDIDATES = ["v10", "10m_v_component_of_wind", "wind_v", "v_wind", "v", "V10M", "v10m"]

CURRENT_U_CANDIDATES = ["uo", "water_u", "curr_u", "u_current", "u", "uo_surface"]
CURRENT_V_CANDIDATES = ["vo", "water_v", "curr_v", "v_current", "v", "vo_surface"]

WAVE_H_CANDIDATES = ["vhm0", "swh", "hs", "wave_height", "htsgw"]
WAVE_P_CANDIDATES = ["vped", "vtm02", "mwp", "wave_period", "perpw"]
WAVE_D_CANDIDATES = ["vmdr", "mwd", "wave_direction", "dirpw"]


class GenericForcingReader:
    """Extracts and normalizes forcing grids from gridded files."""

    @classmethod
    def find_variable(cls, var_dict: Dict[str, Any], candidates: List[str]) -> Optional[str]:
        """Finds matching variable key (case-insensitive) from candidates."""
        lowered = {k.lower(): k for k in var_dict.keys()}
        for cand in candidates:
            if cand.lower() in lowered:
                return lowered[cand.lower()]
        return None

    @classmethod
    def parse_netcdf_dataset(
        cls,
        nc_dataset: Any,
        variable_type: str,
        source: str,
        dataset_version: str,
        resolution: str,
        provenance: Optional[ForcingProvenance] = None,
    ) -> NormalizedForcingData:
        """
        Parses an open netCDF4.Dataset or xarray.Dataset into NormalizedForcingData.
        """
        vars_map = nc_dataset.variables

        # 1. Identify coordinates
        lat_var_name = cls.find_variable(vars_map, LAT_CANDIDATES)
        lon_var_name = cls.find_variable(vars_map, LON_CANDIDATES)
        time_var_name = cls.find_variable(vars_map, TIME_CANDIDATES)

        if not lat_var_name or not lon_var_name:
            raise ValueError(f"Could not identify latitude/longitude variables in dataset: {list(vars_map.keys())}")

        lats = np.array(vars_map[lat_var_name][:], dtype=np.float32)
        lons = np.array(vars_map[lon_var_name][:], dtype=np.float32)

        # Handle 2D curvilinear coordinates
        if lats.ndim == 2:
            lats = lats[:, 0]
        if lons.ndim == 2:
            lons = lons[0, :]

        # Extract timestamps
        timestamps: List[str] = []
        if time_var_name and time_var_name in vars_map:
            t_var = vars_map[time_var_name]
            try:
                import netCDF4
                dates = netCDF4.num2date(t_var[:], getattr(t_var, "units", "hours since 1900-01-01"))
                timestamps = [d.isoformat() for d in dates]
            except Exception:
                timestamps = [f"T_{i}" for i in range(len(t_var))]
        else:
            timestamps = ["T_0"]

        # 2. Identify vector variables based on variable_type
        if variable_type == "wind":
            u_name = cls.find_variable(vars_map, WIND_U_CANDIDATES)
            v_name = cls.find_variable(vars_map, WIND_V_CANDIDATES)
        elif variable_type == "current":
            u_name = cls.find_variable(vars_map, CURRENT_U_CANDIDATES)
            v_name = cls.find_variable(vars_map, CURRENT_V_CANDIDATES)
        elif variable_type == "wave":
            u_name = cls.find_variable(vars_map, WIND_U_CANDIDATES + CURRENT_U_CANDIDATES)
            v_name = cls.find_variable(vars_map, WIND_V_CANDIDATES + CURRENT_V_CANDIDATES)
        else:
            raise ValueError(f"Unsupported variable_type: {variable_type}")

        if not u_name or not v_name:
            raise ValueError(
                f"Could not find vector components (u, v) for '{variable_type}' in {list(vars_map.keys())}"
            )

        u_raw = np.array(vars_map[u_name][:])
        v_raw = np.array(vars_map[v_name][:])

        # Squeeze out 4D depth/elevation dimensions if present: [time, depth, lat, lon] -> [time, lat, lon]
        if u_raw.ndim == 4 and u_raw.shape[1] == 1:
            u_raw = u_raw.squeeze(axis=1)
            v_raw = v_raw.squeeze(axis=1)

        # Replace fill values with NaN
        u_raw = np.where(np.abs(u_raw) > 1e10, np.nan, u_raw)
        v_raw = np.where(np.abs(v_raw) > 1e10, np.nan, v_raw)

        # Optional wave metrics
        wave_h = None
        wave_p = None
        wave_d = None
        h_name = cls.find_variable(vars_map, WAVE_H_CANDIDATES)
        p_name = cls.find_variable(vars_map, WAVE_P_CANDIDATES)
        d_name = cls.find_variable(vars_map, WAVE_D_CANDIDATES)

        if h_name:
            wave_h = np.array(vars_map[h_name][:])
            if wave_h.ndim == 4 and wave_h.shape[1] == 1:
                wave_h = wave_h.squeeze(axis=1)
        if p_name:
            wave_p = np.array(vars_map[p_name][:])
            if wave_p.ndim == 4 and wave_p.shape[1] == 1:
                wave_p = wave_p.squeeze(axis=1)
        if d_name:
            wave_d = np.array(vars_map[d_name][:])
            if wave_d.ndim == 4 and wave_d.shape[1] == 1:
                wave_d = wave_d.squeeze(axis=1)

        return NormalizedForcingData(
            variable_type=variable_type,
            timestamp=timestamps,
            latitude=lats.tolist(),
            longitude=lons.tolist(),
            u=u_raw,
            v=v_raw,
            source=source,
            dataset_version=dataset_version,
            resolution=resolution,
            provenance=provenance,
            wave_height_m=wave_h,
            wave_period_s=wave_p,
            wave_direction_deg=wave_d,
        )

    @classmethod
    def read_netcdf_file(
        cls,
        file_path: Union[str, Path],
        variable_type: str,
        source: str,
        dataset_version: str,
        resolution: str,
        provenance: Optional[ForcingProvenance] = None,
    ) -> NormalizedForcingData:
        """Reads NetCDF file from disk into NormalizedForcingData."""
        import netCDF4
        ds = netCDF4.Dataset(str(file_path), "r")
        try:
            return cls.parse_netcdf_dataset(
                nc_dataset=ds,
                variable_type=variable_type,
                source=source,
                dataset_version=dataset_version,
                resolution=resolution,
                provenance=provenance,
            )
        finally:
            ds.close()
