"""
SlickTrace v2 — Ocean Physics & Reader Tests
"""
import pytest
from ocean.readers.base import OceanDataUnavailable
from ocean.readers.era5_reader import ERA5Reader
from ocean.readers.cmems_reader import CMEMSReader
from ocean.readers.incois_reader import INCOISReader


def test_era5_unconfigured_availability():
    reader = ERA5Reader()
    # If CDS_KEY is empty in test environment, check_availability must return False
    reader._cds_key = ""
    ok, reason = reader.check_availability()
    assert ok is False
    assert "CDS_KEY not configured" in reason


def test_cmems_unconfigured_availability():
    reader = CMEMSReader()
    reader._username = ""
    reader._password = ""
    ok, reason = reader.check_availability()
    assert ok is False
    assert "CMEMS_USERNAME" in reason


def test_incois_stub_returns_unavailable():
    reader = INCOISReader()
    ok, reason = reader.check_availability()
    assert ok is False
    assert "INCOIS adapter is a stub" in reason

    with pytest.raises(OceanDataUnavailable) as exc:
        reader.fetch_wind(0, 0, 1, 1, "2026-01-01", "2026-01-02", None)
    assert "[UNAVAILABLE]" in str(exc.value)
