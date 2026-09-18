"""
SlickTrace v2 — INCOIS Stub Adapter

Stub for Indian National Centre for Ocean Information Services (INCOIS/ESSO).
Currently UNAVAILABLE — credentials and API documentation required.

This stub implements the OceanReader interface so the rest of the system
can reference it without crashing. When credentials are provided and the
API spec is confirmed, implement fetch_currents() and fetch_wind() here.
"""
from __future__ import annotations

import os
from pathlib import Path

from ocean.readers.base import OceanDataUnavailable, OceanReader


class INCOISReader(OceanReader):
    source_name = "INCOIS (ESSO)"
    requires_credentials = True

    STUB_MESSAGE = (
        "INCOIS adapter is a stub. "
        "Credentials (INCOIS_API_URL + INCOIS_API_KEY) and API documentation "
        "are required to implement this reader. "
        "Contact: https://incois.gov.in/"
    )

    def __init__(self):
        self._api_url = os.environ.get("INCOIS_API_URL", "").strip()
        self._api_key = os.environ.get("INCOIS_API_KEY", "").strip()

    def check_availability(self) -> tuple[bool, str]:
        return False, self.STUB_MESSAGE

    def fetch_wind(self, *args, **kwargs) -> Path:
        raise OceanDataUnavailable(
            source=self.source_name,
            reason=self.STUB_MESSAGE,
            registration_url="https://incois.gov.in/",
        )

    def fetch_currents(self, *args, **kwargs) -> Path:
        raise OceanDataUnavailable(
            source=self.source_name,
            reason=self.STUB_MESSAGE,
            registration_url="https://incois.gov.in/",
        )
