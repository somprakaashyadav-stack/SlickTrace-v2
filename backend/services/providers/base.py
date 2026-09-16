from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DataProvider(ABC):
    """Master Base Class for all SlickTrace Data Providers."""
    pass

class SatelliteProvider(DataProvider):
    @abstractmethod
    def fetch_raw_scene_data(self, scene_id: str) -> Dict[str, Any]:
        """Fetches raw satellite imagery and metadata."""
        pass

    @abstractmethod
    def get_granule_metadata(self, scene_id: str) -> Dict[str, Any]:
        """Fetches metadata for a given granule."""
        pass

class AISProvider(DataProvider):
    @abstractmethod
    def get_ais_tracks(self, time_window_start: str, time_window_end: str, bbox: List[float]) -> List[Dict[str, Any]]:
        """Fetches AIS tracks within a space-time window."""
        pass

class MetoceanProvider(DataProvider):
    @abstractmethod
    def get_wind_and_currents(self, lat: float, lon: float, timestamp: str) -> Dict[str, Any]:
        """Fetches wind and ocean current data for a given point and time."""
        pass
