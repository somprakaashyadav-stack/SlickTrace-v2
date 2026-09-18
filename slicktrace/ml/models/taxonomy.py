"""
SlickTrace v2 — Remote-Sensing Classification Taxonomy

Defines the 8 standardized classification classes for marine surface dark formations:
- OIL_SLICK: Genuine hydrocarbon slick (mineral oil)
- ALGAE_LIKE: Biogenic slick / algal bloom / organic film
- SHIP_WAKE: Vessel turbulence or Kelvin wake dark strip
- LOW_WIND_DARK_AREA: Atmospheric calm / wind shadow area (< 3 m/s)
- COASTAL_ARTIFACT: Land-sea boundary masking artifact or bathymetric damping
- CLOUD: Optical cloud shadow / convective masking
- WATER: Normal open water background sea clutter
- UNKNOWN: Unresolved dark formation
"""
from enum import Enum
from typing import Dict


class SpillClass(str, Enum):
    OIL_SLICK = "OIL_SLICK"
    ALGAE_LIKE = "ALGAE_LIKE"
    SHIP_WAKE = "SHIP_WAKE"
    LOW_WIND_DARK_AREA = "LOW_WIND_DARK_AREA"
    COASTAL_ARTIFACT = "COASTAL_ARTIFACT"
    CLOUD = "CLOUD"
    WATER = "WATER"
    UNKNOWN = "UNKNOWN"


CLASS_METADATA: Dict[SpillClass, Dict[str, str]] = {
    SpillClass.OIL_SLICK: {
        "description": "Confirmed mineral oil slick (hydrocarbon damping)",
        "color": "#ef4444",
        "action": "Trigger ocean drift hindcast & AIS candidate attribution",
    },
    SpillClass.ALGAE_LIKE: {
        "description": "Biogenic slick / natural organic surfactant / algal bloom",
        "color": "#10b981",
        "action": "Monitor; low environmental prosecution risk",
    },
    SpillClass.SHIP_WAKE: {
        "description": "Turbulent or Kelvin ship wake trail",
        "color": "#3b82f6",
        "action": "Correlate with vessel AIS track geometry",
    },
    SpillClass.LOW_WIND_DARK_AREA: {
        "description": "Atmospheric wind calm / wind shadow area",
        "color": "#6b7280",
        "action": "Validate against ERA5 10m wind speed vectors",
    },
    SpillClass.COASTAL_ARTIFACT: {
        "description": "Shallow bathymetry or shoreline mask artifact",
        "color": "#f59e0b",
        "action": "Apply high-resolution land-sea boundary mask",
    },
    SpillClass.CLOUD: {
        "description": "Optical convective cloud shadow",
        "color": "#9ca3af",
        "action": "Cross-reference with Sentinel-2 cloud mask / Sentinel-1 SAR",
    },
    SpillClass.WATER: {
        "description": "Clean open sea surface clutter",
        "color": "#0284c7",
        "action": "No anomalous damping detected",
    },
    SpillClass.UNKNOWN: {
        "description": "Unresolved dark formation",
        "color": "#8b5cf6",
        "action": "Requires auxiliary SAR pass or sensor cross-validation",
    },
}
