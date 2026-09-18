"""
SlickTrace v2 — Environmental Forcing Cache & Provenance Storage Manager

Provides:
- Deterministic cache key generation based on spatiotemporal query parameters
- Raw file and normalized data caching under data/ocean/cache/
- SHA-256 integrity verification
- Cache hit/miss management preventing redundant satellite/weather downloads
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from ocean.forcing.models import AOI, ForcingProvenance, NormalizedForcingData


DEFAULT_CACHE_DIR = Path(os.environ.get("FORCING_CACHE_DIR", "data/ocean/cache"))


class ForcingCacheManager:
    """Manages disk caching and integrity verification for environmental forcing products."""

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def compute_cache_key(
        cls,
        variable_type: str,
        source: str,
        aoi: AOI,
        start_time: str,
        end_time: str,
    ) -> str:
        """
        Generates a deterministic SHA-256 hash identifying the query slice.
        """
        canonical_str = (
            f"{variable_type.lower()}|"
            f"{source.lower()}|"
            f"{aoi.lon_min:.4f}_{aoi.lat_min:.4f}_{aoi.lon_max:.4f}_{aoi.lat_max:.4f}|"
            f"{start_time}|{end_time}"
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def get_cache_paths(self, cache_key: str) -> Dict[str, Path]:
        """Returns standard file paths associated with a given cache key."""
        base = self.cache_dir / cache_key
        return {
            "raw_nc": base.with_suffix(".nc"),
            "meta_json": base.with_suffix(".json"),
            "data_npz": base.with_suffix(".npz"),
        }

    def has(self, cache_key: str) -> bool:
        """Returns True if normalized data is cached and valid."""
        paths = self.get_cache_paths(cache_key)
        return paths["meta_json"].exists() and paths["data_npz"].exists()

    def get_raw_file(self, cache_key: str) -> Optional[Path]:
        """Returns path to cached NetCDF if it exists."""
        p = self.get_cache_paths(cache_key)["raw_nc"]
        return p if p.exists() else None

    def store_raw_file(self, cache_key: str, src_path: Path) -> Tuple[Path, str]:
        """
        Stores a downloaded raw forcing file (NetCDF/GRIB) into cache and returns (path, sha256).
        """
        dest_path = self.get_cache_paths(cache_key)["raw_nc"]
        shutil.copy2(str(src_path), str(dest_path))

        # Compute SHA-256
        h = hashlib.sha256()
        with open(dest_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        file_sha256 = h.hexdigest()

        return dest_path, file_sha256

    def store_normalized(self, cache_key: str, data: NormalizedForcingData) -> None:
        """Caches normalized data arrays (as compressed npz) and metadata json."""
        paths = self.get_cache_paths(cache_key)

        # Save binary arrays compressed
        np.savez_compressed(
            paths["data_npz"],
            u=data.u,
            v=data.v,
            lat=data.latitude,
            lon=data.longitude,
            wave_height=data.wave_height_m if data.wave_height_m is not None else np.array([]),
            wave_period=data.wave_period_s if data.wave_period_s is not None else np.array([]),
            wave_direction=data.wave_direction_deg if data.wave_direction_deg is not None else np.array([]),
        )

        # Save metadata
        meta = {
            "variable_type": data.variable_type,
            "source": data.source,
            "dataset_version": data.dataset_version,
            "resolution": data.resolution,
            "timestamp": list(data.timestamp),
            "provenance": data.provenance.to_dict() if data.provenance else None,
        }
        with open(paths["meta_json"], "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def get_normalized(self, cache_key: str) -> Optional[NormalizedForcingData]:
        """Loads cached NormalizedForcingData if available."""
        if not self.has(cache_key):
            return None

        paths = self.get_cache_paths(cache_key)
        try:
            with open(paths["meta_json"], "r", encoding="utf-8") as f:
                meta = json.load(f)

            npz = np.load(paths["data_npz"])
            u = npz["u"]
            v = npz["v"]
            lat = npz["lat"]
            lon = npz["lon"]

            wave_h = npz["wave_height"] if "wave_height" in npz and npz["wave_height"].size > 0 else None
            wave_p = npz["wave_period"] if "wave_period" in npz and npz["wave_period"].size > 0 else None
            wave_d = npz["wave_direction"] if "wave_direction" in npz and npz["wave_direction"].size > 0 else None

            prov = None
            if meta.get("provenance"):
                prov = ForcingProvenance(**meta["provenance"])

            return NormalizedForcingData(
                variable_type=meta["variable_type"],
                timestamp=meta["timestamp"],
                latitude=lat,
                longitude=lon,
                u=u,
                v=v,
                source=meta["source"],
                dataset_version=meta["dataset_version"],
                resolution=meta["resolution"],
                provenance=prov,
                wave_height_m=wave_h,
                wave_period_s=wave_p,
                wave_direction_deg=wave_d,
            )
        except Exception:
            return None

    def clear(self) -> int:
        """Clears all cached forcing files."""
        count = 0
        for f in self.cache_dir.glob("*"):
            if f.is_file():
                f.unlink()
                count += 1
        return count
