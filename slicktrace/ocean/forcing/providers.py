"""
SlickTrace v2 — Environmental Forcing Providers

Implements:
- WindProvider: Primary ERA5 hourly 10m wind via Copernicus CDS API.
- CurrentProvider: Primary Copernicus Marine (CMEMS); Optional HYCOM/INCOIS fallbacks.
- WaveProvider: Primary Copernicus Marine Global Ocean Waves / ERA5 wave spectra.

Strict Real-Data Contract:
- Never silently substitutes unrelated environmental data.
- Unconfigured sources raise OceanDataUnavailable with registration guidance.
- Fallback sources are strictly tracked in metadata and provenance with the true source name.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ocean.forcing.cache import ForcingCacheManager
from ocean.forcing.generic_reader import GenericForcingReader
from ocean.forcing.models import (
    AOI,
    ForcingProvenance,
    NormalizedForcingData,
    parse_aoi,
)
from ocean.readers.base import OceanDataUnavailable
from ocean.readers.cmems_reader import CMEMSReader
from ocean.readers.era5_reader import ERA5Reader
from ocean.readers.hycom_reader import HYCOMReader
from ocean.readers.incois_reader import INCOISReader


class WindProvider:
    """
    Environmental forcing provider for wind fields.
    Primary: ERA5 hourly 10m wind (ECMWF CDS).
    """

    def __init__(self, cache_manager: Optional[ForcingCacheManager] = None):
        self.cache = cache_manager or ForcingCacheManager()
        self.era5_reader = ERA5Reader()

    def check_availability(self) -> Tuple[bool, str]:
        """Checks if primary wind provider (ERA5) is configured."""
        return self.era5_reader.check_availability()

    def get_wind(
        self,
        aoi: Union[AOI, Tuple[float, float, float, float], List[float], Dict[str, float], Any],
        start: str,
        end: str,
        use_cache: bool = True,
    ) -> NormalizedForcingData:
        """
        Retrieves normalized 10m wind forcing (u, v) for the given AOI and time window.
        Primary: ERA5 hourly reanalysis.
        """
        parsed_aoi = parse_aoi(aoi)
        cache_key = self.cache.compute_cache_key("wind", "ERA5", parsed_aoi, start, end)

        # 1. Check cache
        if use_cache:
            cached = self.cache.get_normalized(cache_key)
            if cached is not None:
                return cached

        # 2. Check credentials & availability (Never fabricate!)
        ok, reason = self.check_availability()
        if not ok:
            raise OceanDataUnavailable(
                source=self.era5_reader.source_name,
                reason=reason,
                registration_url="https://cds.climate.copernicus.eu/",
            )

        # 3. Fetch from CDS API
        t0 = time.time()
        temp_nc = self.cache.cache_dir / f"tmp_era5_{cache_key[:12]}.nc"

        try:
            self.era5_reader.fetch_wind(
                lon_min=parsed_aoi.lon_min,
                lat_min=parsed_aoi.lat_min,
                lon_max=parsed_aoi.lon_max,
                lat_max=parsed_aoi.lat_max,
                time_start=start,
                time_end=end,
                output_path=temp_nc,
            )

            # Store in cache and compute SHA-256
            stored_nc, file_sha256 = self.cache.store_raw_file(cache_key, temp_nc)
            duration = round(time.time() - t0, 3)

            provenance = ForcingProvenance(
                source_name=self.era5_reader.source_name,
                dataset_id="reanalysis-era5-single-levels",
                dataset_version="ERA5_hourly_10m_v1",
                source_url="https://cds.climate.copernicus.eu/api/v2",
                raw_file_sha256=file_sha256,
                spatial_bounds=parsed_aoi.to_dict(),
                time_range={"start": start, "end": end},
                execution_duration_sec=duration,
                notes=["Retrieved via ECMWF Climate Data Store (CDS) API."],
            )

            normalized = GenericForcingReader.read_netcdf_file(
                file_path=stored_nc,
                variable_type="wind",
                source="ERA5",
                dataset_version="ERA5_hourly_10m_v1",
                resolution="0.25 deg, 1h",
                provenance=provenance,
            )

            self.cache.store_normalized(cache_key, normalized)
            return normalized

        finally:
            if temp_nc.exists():
                try:
                    temp_nc.unlink()
                except Exception:
                    pass


class CurrentProvider:
    """
    Environmental forcing provider for ocean currents.
    Primary: Copernicus Marine Service (CMEMS) Global Ocean Analysis and Forecast.
    Optional Fallback: HYCOM GLBv0.08 (Public THREDDS OPeNDAP).
    Optional Regional: INCOIS stub.
    """

    def __init__(self, cache_manager: Optional[ForcingCacheManager] = None):
        self.cache = cache_manager or ForcingCacheManager()
        self.cmems_reader = CMEMSReader()
        self.hycom_reader = HYCOMReader()
        self.incois_reader = INCOISReader()

    def check_availability(self) -> Tuple[bool, str]:
        """Checks if primary currents provider (CMEMS) is configured."""
        return self.cmems_reader.check_availability()

    def get_currents(
        self,
        aoi: Union[AOI, Tuple[float, float, float, float], List[float], Dict[str, float], Any],
        start: str,
        end: str,
        allow_fallback: bool = False,
        use_cache: bool = True,
    ) -> NormalizedForcingData:
        """
        Retrieves surface ocean currents (uo, vo) for given AOI and time window.
        If allow_fallback is True and CMEMS is unavailable, queries HYCOM and records HYCOM in provenance.
        """
        parsed_aoi = parse_aoi(aoi)

        # 1. Attempt Primary: CMEMS
        cmems_available, cmems_reason = self.cmems_reader.check_availability()

        if cmems_available:
            cache_key = self.cache.compute_cache_key("current", "CMEMS", parsed_aoi, start, end)
            if use_cache:
                cached = self.cache.get_normalized(cache_key)
                if cached is not None:
                    return cached

            t0 = time.time()
            temp_nc = self.cache.cache_dir / f"tmp_cmems_{cache_key[:12]}.nc"
            try:
                self.cmems_reader.fetch_currents(
                    lon_min=parsed_aoi.lon_min,
                    lat_min=parsed_aoi.lat_min,
                    lon_max=parsed_aoi.lon_max,
                    lat_max=parsed_aoi.lat_max,
                    time_start=start,
                    time_end=end,
                    output_path=temp_nc,
                )
                stored_nc, file_sha256 = self.cache.store_raw_file(cache_key, temp_nc)
                duration = round(time.time() - t0, 3)

                provenance = ForcingProvenance(
                    source_name=self.cmems_reader.source_name,
                    dataset_id=CMEMSReader.DATASET_ID,
                    dataset_version="CMEMS_GLOBAL_ANALYSIS_FORECAST_PHY_001_024",
                    source_url="https://marine.copernicus.eu/",
                    raw_file_sha256=file_sha256,
                    spatial_bounds=parsed_aoi.to_dict(),
                    time_range={"start": start, "end": end},
                    execution_duration_sec=duration,
                    notes=["Primary CMEMS ocean current subset."],
                )

                normalized = GenericForcingReader.read_netcdf_file(
                    file_path=stored_nc,
                    variable_type="current",
                    source="CMEMS",
                    dataset_version="CMEMS_PHY_0.083deg_P1D",
                    resolution="0.083 deg, 24h",
                    provenance=provenance,
                )
                self.cache.store_normalized(cache_key, normalized)
                return normalized
            finally:
                if temp_nc.exists():
                    try:
                        temp_nc.unlink()
                    except Exception:
                        pass

        # If CMEMS is not available:
        if not allow_fallback:
            raise OceanDataUnavailable(
                source=self.cmems_reader.source_name,
                reason=cmems_reason,
                registration_url="https://marine.copernicus.eu/",
            )

        # 2. Fallback: HYCOM (Public THREDDS)
        cache_key = self.cache.compute_cache_key("current", "HYCOM", parsed_aoi, start, end)
        if use_cache:
            cached = self.cache.get_normalized(cache_key)
            if cached is not None:
                return cached

        hycom_ok, hycom_reason = self.hycom_reader.check_availability()
        if not hycom_ok:
            raise OceanDataUnavailable(
                source=self.hycom_reader.source_name,
                reason=f"CMEMS unavailable ({cmems_reason}); HYCOM fallback unavailable ({hycom_reason})",
                registration_url="https://tds.hycom.org/",
            )

        t0 = time.time()
        temp_nc = self.cache.cache_dir / f"tmp_hycom_{cache_key[:12]}.nc"
        try:
            self.hycom_reader.fetch_currents(
                lon_min=parsed_aoi.lon_min,
                lat_min=parsed_aoi.lat_min,
                lon_max=parsed_aoi.lon_max,
                lat_max=parsed_aoi.lat_max,
                time_start=start,
                time_end=end,
                output_path=temp_nc,
            )
            stored_nc, file_sha256 = self.cache.store_raw_file(cache_key, temp_nc)
            duration = round(time.time() - t0, 3)

            provenance = ForcingProvenance(
                source_name=self.hycom_reader.source_name,
                dataset_id="GLBy0.08_expt_93.0",
                dataset_version="HYCOM_GLBy0.08_OPeNDAP",
                source_url="https://tds.hycom.org/thredds/dodsC/GLBy0.08/expt_93.0",
                raw_file_sha256=file_sha256,
                spatial_bounds=parsed_aoi.to_dict(),
                time_range={"start": start, "end": end},
                execution_duration_sec=duration,
                notes=[
                    f"FALLBACK USED: CMEMS unavailable ({cmems_reason}). "
                    "Data sourced from public HYCOM THREDDS OPeNDAP server."
                ],
            )

            normalized = GenericForcingReader.read_netcdf_file(
                file_path=stored_nc,
                variable_type="current",
                source="HYCOM",
                dataset_version="HYCOM_GLBv0.08",
                resolution="0.08 deg, 3h",
                provenance=provenance,
            )
            self.cache.store_normalized(cache_key, normalized)
            return normalized
        finally:
            if temp_nc.exists():
                try:
                    temp_nc.unlink()
                except Exception:
                    pass


class WaveProvider:
    """
    Environmental forcing provider for ocean waves & Stokes drift.
    Primary: Copernicus Marine Global Ocean Waves (cmems_mod_glo_wav_anfc_0.083deg_PT3H-i) or ERA5 wave spectra.
    """

    DATASET_ID = "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i"

    def __init__(self, cache_manager: Optional[ForcingCacheManager] = None):
        self.cache = cache_manager or ForcingCacheManager()
        self._username = os.environ.get("CMEMS_USERNAME", "").strip()
        self._password = os.environ.get("CMEMS_PASSWORD", "").strip()

    def check_availability(self) -> Tuple[bool, str]:
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

    def get_waves(
        self,
        aoi: Union[AOI, Tuple[float, float, float, float], List[float], Dict[str, float], Any],
        start: str,
        end: str,
        use_cache: bool = True,
    ) -> NormalizedForcingData:
        """
        Retrieves wave fields (significant wave height, mean wave period, direction)
        and computes effective Stokes drift vectors (u, v).
        """
        parsed_aoi = parse_aoi(aoi)
        cache_key = self.cache.compute_cache_key("wave", "CMEMS_WAVE", parsed_aoi, start, end)

        if use_cache:
            cached = self.cache.get_normalized(cache_key)
            if cached is not None:
                return cached

        ok, reason = self.check_availability()
        if not ok:
            raise OceanDataUnavailable(
                source="Copernicus Marine Waves",
                reason=reason,
                registration_url="https://marine.copernicus.eu/",
            )

        import copernicusmarine
        t0 = time.time()
        temp_nc = self.cache.cache_dir / f"tmp_wave_{cache_key[:12]}.nc"

        try:
            copernicusmarine.subset(
                dataset_id=self.DATASET_ID,
                variables=["VHM0", "VMDR", "VPED"],
                minimum_longitude=parsed_aoi.lon_min,
                maximum_longitude=parsed_aoi.lon_max,
                minimum_latitude=parsed_aoi.lat_min,
                maximum_latitude=parsed_aoi.lat_max,
                start_datetime=start,
                end_datetime=end,
                output_filename=str(temp_nc),
                username=self._username,
                password=self._password,
                force_download=True,
            )

            stored_nc, file_sha256 = self.cache.store_raw_file(cache_key, temp_nc)
            duration = round(time.time() - t0, 3)

            provenance = ForcingProvenance(
                source_name="Copernicus Marine Waves",
                dataset_id=self.DATASET_ID,
                dataset_version="CMEMS_WAV_0.083deg_PT3H",
                source_url="https://marine.copernicus.eu/",
                raw_file_sha256=file_sha256,
                spatial_bounds=parsed_aoi.to_dict(),
                time_range={"start": start, "end": end},
                execution_duration_sec=duration,
                notes=["Copernicus Marine Global Ocean Wave Analysis & Forecast."],
            )

            normalized = GenericForcingReader.read_netcdf_file(
                file_path=stored_nc,
                variable_type="wave",
                source="CMEMS_WAVE",
                dataset_version="CMEMS_WAV_0.083deg_PT3H",
                resolution="0.083 deg, 3h",
                provenance=provenance,
            )

            # Compute approximate Stokes drift vectors (m/s) from wave height and period
            # u_stokes ~ 0.015 * H_s / T_p in wave direction
            if normalized.wave_height_m is not None and normalized.wave_period_s is not None and normalized.wave_direction_deg is not None:
                hs = normalized.wave_height_m
                tp = np.where(normalized.wave_period_s == 0, 1.0, normalized.wave_period_s)
                theta_rad = np.radians(normalized.wave_direction_deg)
                stokes_mag = 0.015 * (hs / tp)
                normalized.u = stokes_mag * np.sin(theta_rad)
                normalized.v = stokes_mag * np.cos(theta_rad)

            self.cache.store_normalized(cache_key, normalized)
            return normalized

        finally:
            if temp_nc.exists():
                try:
                    temp_nc.unlink()
                except Exception:
                    pass
