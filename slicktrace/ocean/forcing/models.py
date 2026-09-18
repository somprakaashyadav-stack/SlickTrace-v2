"""
SlickTrace v2 — Environmental Forcing Models & Normalized Representation

Defines:
- AOI: Standardized Area of Interest parser & validator
- ForcingProvenance: Full cryptographic & operational traceability record
- NormalizedForcingData: Standardized internal model for wind, ocean currents, and waves
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class AOI:
    """Standardized Area of Interest bounding box (WGS84)."""
    lon_min: float
    lat_min: float
    lon_max: float
    lat_max: float

    def __post_init__(self):
        if self.lon_min > self.lon_max:
            raise ValueError(f"lon_min ({self.lon_min}) cannot exceed lon_max ({self.lon_max})")
        if self.lat_min > self.lat_max:
            raise ValueError(f"lat_min ({self.lat_min}) cannot exceed lat_max ({self.lat_max})")
        if not (-180.0 <= self.lon_min <= 180.0 and -180.0 <= self.lon_max <= 180.0):
            raise ValueError(f"Longitudes must be within [-180, 180]: {self.lon_min}, {self.lon_max}")
        if not (-90.0 <= self.lat_min <= 90.0 and -90.0 <= self.lat_max <= 90.0):
            raise ValueError(f"Latitudes must be within [-90, 90]: {self.lat_min}, {self.lat_max}")

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.lon_min, self.lat_min, self.lon_max, self.lat_max)

    def to_dict(self) -> Dict[str, float]:
        return {
            "lon_min": round(self.lon_min, 6),
            "lat_min": round(self.lat_min, 6),
            "lon_max": round(self.lon_max, 6),
            "lat_max": round(self.lat_max, 6),
        }

    def to_geojson_polygon(self) -> Dict[str, Any]:
        return {
            "type": "Polygon",
            "coordinates": [[
                [self.lon_min, self.lat_min],
                [self.lon_max, self.lat_min],
                [self.lon_max, self.lat_max],
                [self.lon_min, self.lat_max],
                [self.lon_min, self.lat_min],
            ]],
        }


def parse_aoi(aoi: Union[AOI, Tuple[float, float, float, float], List[float], Dict[str, float], Any]) -> AOI:
    """
    Parses various AOI input formats into an AOI instance:
    - AOI instance
    - (lon_min, lat_min, lon_max, lat_max)
    - Dict with keys {lon_min, lat_min, lon_max, lat_max} or {min_lon, min_lat, max_lon, max_lat}
    - GeoJSON polygon dict
    """
    if isinstance(aoi, AOI):
        return aoi

    if isinstance(aoi, (tuple, list)):
        if len(aoi) != 4:
            raise ValueError(f"Expected 4 elements (lon_min, lat_min, lon_max, lat_max), got {len(aoi)}")
        return AOI(float(aoi[0]), float(aoi[1]), float(aoi[2]), float(aoi[3]))

    if isinstance(aoi, dict):
        if "type" in aoi and aoi.get("type") in ("Polygon", "Feature"):
            coords = aoi.get("coordinates") if aoi.get("type") == "Polygon" else aoi.get("geometry", {}).get("coordinates")
            if coords and len(coords) > 0:
                ring = coords[0]
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                return AOI(min(lons), min(lats), max(lons), max(lats))

        lon_min = aoi.get("lon_min", aoi.get("min_lon"))
        lat_min = aoi.get("lat_min", aoi.get("min_lat"))
        lon_max = aoi.get("lon_max", aoi.get("max_lon"))
        lat_max = aoi.get("lat_max", aoi.get("max_lat"))

        if all(v is not None for v in [lon_min, lat_min, lon_max, lat_max]):
            return AOI(float(lon_min), float(lat_min), float(lon_max), float(lat_max))

    raise ValueError(f"Unable to parse AOI from: {aoi}")


@dataclass
class ForcingProvenance:
    """Cryptographic and operational traceability record for environmental data."""
    source_name: str
    dataset_id: str
    dataset_version: str
    source_url: str
    raw_file_sha256: str
    spatial_bounds: Dict[str, float]
    time_range: Dict[str, str]
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_duration_sec: float = 0.0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedForcingData:
    """
    Standard internal representation for environmental forcing data.
    Accommodates 10m wind, surface currents, and wave fields.
    """
    variable_type: str  # 'wind' | 'current' | 'wave'
    timestamp: List[str]  # ISO-8601 timestamps
    latitude: List[float]  # 1D latitude coordinates (degrees)
    longitude: List[float]  # 1D longitude coordinates (degrees)
    u: Union[np.ndarray, List[Any]]  # Eastward velocity / direction component (m/s)
    v: Union[np.ndarray, List[Any]]  # Northward velocity / direction component (m/s)
    source: str  # e.g., 'ERA5', 'CMEMS', 'HYCOM', 'INCOIS'
    dataset_version: str  # Exact dataset identifier or version tag
    resolution: str  # e.g., '0.25 deg, 1h' or '0.083 deg, 24h'
    provenance: Optional[ForcingProvenance] = None

    # Optional wave parameters
    wave_height_m: Optional[Union[np.ndarray, List[Any]]] = None
    wave_period_s: Optional[Union[np.ndarray, List[Any]]] = None
    wave_direction_deg: Optional[Union[np.ndarray, List[Any]]] = None

    def __post_init__(self):
        if self.variable_type not in ("wind", "current", "wave"):
            raise ValueError(f"Unknown variable_type: '{self.variable_type}'. Must be 'wind', 'current', or 'wave'.")

        # Convert lists to numpy arrays internally for calculation efficiency
        if not isinstance(self.latitude, np.ndarray):
            self.latitude = np.array(self.latitude, dtype=np.float32)
        if not isinstance(self.longitude, np.ndarray):
            self.longitude = np.array(self.longitude, dtype=np.float32)
        if not isinstance(self.u, np.ndarray):
            self.u = np.array(self.u, dtype=np.float32)
        if not isinstance(self.v, np.ndarray):
            self.v = np.array(self.v, dtype=np.float32)

    def magnitude(self) -> np.ndarray:
        """Returns speed / magnitude in m/s: sqrt(u^2 + v^2)."""
        return np.sqrt(self.u ** 2 + self.v ** 2)

    def direction(self) -> np.ndarray:
        """
        Returns direction in degrees [0, 360) towards which vector points (oceanographic convention).
        """
        rad = np.arctan2(self.u, self.v)
        deg = np.degrees(rad)
        return (deg + 360.0) % 360.0

    def get_point(self, lat: float, lon: float, time_idx: int = 0) -> Tuple[float, float, float]:
        """
        Extracts nearest-neighbor (u, v, magnitude) for a single spatial coordinate.
        Returns: (u, v, speed) in m/s.
        """
        lat_idx = int(np.argmin(np.abs(self.latitude - lat)))
        lon_idx = int(np.argmin(np.abs(self.longitude - lon)))

        if self.u.ndim == 3:
            t_idx = min(max(time_idx, 0), self.u.shape[0] - 1)
            u_val = float(self.u[t_idx, lat_idx, lon_idx])
            v_val = float(self.v[t_idx, lat_idx, lon_idx])
        elif self.u.ndim == 2:
            u_val = float(self.u[lat_idx, lon_idx])
            v_val = float(self.v[lat_idx, lon_idx])
        else:
            u_val = float(self.u[0])
            v_val = float(self.v[0])

        speed = float(math.sqrt(u_val ** 2 + v_val ** 2))
        return u_val, v_val, speed

    def to_dict(self) -> Dict[str, Any]:
        """Converts normalized forcing data to JSON-serializable dictionary."""
        return {
            "variable_type": self.variable_type,
            "source": self.source,
            "dataset_version": self.dataset_version,
            "resolution": self.resolution,
            "timestamp": list(self.timestamp),
            "latitude": [round(float(x), 5) for x in self.latitude],
            "longitude": [round(float(x), 5) for x in self.longitude],
            "shape": list(self.u.shape),
            "speed_min_ms": round(float(np.nanmin(self.magnitude())), 3) if self.u.size > 0 else 0.0,
            "speed_max_ms": round(float(np.nanmax(self.magnitude())), 3) if self.u.size > 0 else 0.0,
            "speed_mean_ms": round(float(np.nanmean(self.magnitude())), 3) if self.u.size > 0 else 0.0,
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }
