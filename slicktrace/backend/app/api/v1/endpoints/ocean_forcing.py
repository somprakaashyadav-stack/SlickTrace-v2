"""
SlickTrace v2 — Environmental Forcing REST Endpoints

Provides:
- POST /ocean/wind: Query and normalize ERA5 10m wind fields
- POST /ocean/currents: Query and normalize CMEMS / HYCOM ocean currents
- POST /ocean/waves: Query and normalize CMEMS ocean wave fields
- GET /ocean/status: Live provider readiness and credential verification
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.ocean_forcing import (
    ForcingQueryRequest,
    NormalizedForcingResponse,
    ProviderStatusResponse,
)
from ocean.forcing.models import AOI
from ocean.forcing.providers import CurrentProvider, WaveProvider, WindProvider
from ocean.readers.base import OceanDataUnavailable

router = APIRouter()


@router.get("/status", response_model=ProviderStatusResponse)
async def get_providers_status():
    """Returns availability and credential health of environmental forcing providers."""
    wp = WindProvider()
    cp = CurrentProvider()
    wavp = WaveProvider()

    era5_ok, era5_reason = wp.check_availability()
    cmems_cur_ok, cmems_cur_reason = cp.check_availability()
    hycom_ok, hycom_reason = cp.hycom_reader.check_availability()
    incois_ok, incois_reason = cp.incois_reader.check_availability()
    cmems_wav_ok, cmems_wav_reason = wavp.check_availability()

    return ProviderStatusResponse(
        era5_wind={"available": era5_ok, "status": era5_reason},
        cmems_currents={"available": cmems_cur_ok, "status": cmems_cur_reason},
        hycom_currents={"available": hycom_ok, "status": hycom_reason},
        incois_currents={"available": incois_ok, "status": incois_reason},
        cmems_waves={"available": cmems_wav_ok, "status": cmems_wav_reason},
    )


@router.post("/wind", response_model=NormalizedForcingResponse)
async def get_wind_forcing(payload: ForcingQueryRequest):
    """
    Query and normalize primary 10m wind forcing (ERA5).
    Raises 503 if credentials unconfigured — never fabricates synthetic wind.
    """
    wp = WindProvider()
    aoi = AOI(lon_min=payload.lon_min, lat_min=payload.lat_min, lon_max=payload.lon_max, lat_max=payload.lat_max)

    try:
        data = wp.get_wind(
            aoi=aoi,
            start=payload.time_start,
            end=payload.time_end,
            use_cache=payload.use_cache,
        )
        return data.to_dict()
    except OceanDataUnavailable as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "EnvironmentalProviderUnavailable",
                "source": e.source,
                "reason": e.reason,
                "registration_url": e.registration_url,
            },
        )


@router.post("/currents", response_model=NormalizedForcingResponse)
async def get_currents_forcing(payload: ForcingQueryRequest):
    """
    Query and normalize ocean current forcing (CMEMS primary, HYCOM optional fallback).
    Raises 503 if unavailable — never substitutes unrelated data without explicit fallback.
    """
    cp = CurrentProvider()
    aoi = AOI(lon_min=payload.lon_min, lat_min=payload.lat_min, lon_max=payload.lon_max, lat_max=payload.lat_max)

    try:
        data = cp.get_currents(
            aoi=aoi,
            start=payload.time_start,
            end=payload.time_end,
            allow_fallback=payload.allow_fallback,
            use_cache=payload.use_cache,
        )
        return data.to_dict()
    except OceanDataUnavailable as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "EnvironmentalProviderUnavailable",
                "source": e.source,
                "reason": e.reason,
                "registration_url": e.registration_url,
            },
        )


@router.post("/waves", response_model=NormalizedForcingResponse)
async def get_waves_forcing(payload: ForcingQueryRequest):
    """
    Query and normalize ocean wave forcing (CMEMS Waves).
    """
    wavp = WaveProvider()
    aoi = AOI(lon_min=payload.lon_min, lat_min=payload.lat_min, lon_max=payload.lon_max, lat_max=payload.lat_max)

    try:
        data = wavp.get_waves(
            aoi=aoi,
            start=payload.time_start,
            end=payload.time_end,
            use_cache=payload.use_cache,
        )
        return data.to_dict()
    except OceanDataUnavailable as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "EnvironmentalProviderUnavailable",
                "source": e.source,
                "reason": e.reason,
                "registration_url": e.registration_url,
            },
        )
