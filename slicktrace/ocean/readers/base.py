"""
SlickTrace v2 — Abstract Ocean Reader Interface

All ocean data readers (ERA5, CMEMS, HYCOM, INCOIS) implement this interface.
If a reader cannot provide data (missing credentials, network error), it raises
OceanDataUnavailable — never returns None silently.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class OceanDataUnavailable(Exception):
    """
    Raised when an ocean data reader cannot provide data.
    Includes human-readable reason and registration URL if applicable.
    """
    def __init__(self, source: str, reason: str, registration_url: str = ""):
        self.source = source
        self.reason = reason
        self.registration_url = registration_url
        msg = f"[UNAVAILABLE] {source}: {reason}"
        if registration_url:
            msg += f" Register at: {registration_url}"
        super().__init__(msg)


class OceanReader(ABC):
    """Abstract base class for all ocean forcing data readers."""

    source_name: str = "unknown"
    requires_credentials: bool = True

    @abstractmethod
    def check_availability(self) -> tuple[bool, str]:
        """
        Check if this reader can provide data.
        Returns (is_available: bool, reason: str).
        """
        ...

    @abstractmethod
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
        Fetch wind field data as NetCDF and save to output_path.
        Raises OceanDataUnavailable if credentials missing or fetch fails.
        """
        ...

    @abstractmethod
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
        Fetch ocean current data as NetCDF and save to output_path.
        Raises OceanDataUnavailable if credentials missing or fetch fails.
        """
        ...
