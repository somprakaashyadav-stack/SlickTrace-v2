import logging
from backend.config import settings
from backend.services.providers.base import SatelliteProvider, AISProvider, MetoceanProvider
from backend.services.providers.satellite import DemoSatelliteProvider, SentinelProvider
from backend.services.providers.ais import DemoAISProvider, AISRealProvider
from backend.services.providers.metocean import DemoMetoceanProvider, MetoceanRealProvider

logger = logging.getLogger(__name__)

def get_satellite_provider() -> SatelliteProvider:
    if settings.DATA_MODE == "real":
        try:
            return SentinelProvider()
        except Exception as e:
            logger.error(f"Failed to initialize SentinelProvider: {e}")
            # Fallback handled in routes or here. Actually, we return SentinelProvider 
            # and it falls back internally on method call, OR we wrap it here.
            # Best is to return a wrapper or just let SentinelProvider methods fallback.
            # Let's just return SentinelProvider and have its methods raise exception which route catches.
            return SentinelProvider()
    return DemoSatelliteProvider()

def get_ais_provider() -> AISProvider:
    if settings.DATA_MODE == "real":
        return AISRealProvider()
    return DemoAISProvider()

def get_metocean_provider() -> MetoceanProvider:
    if settings.DATA_MODE == "real":
        return MetoceanRealProvider()
    return DemoMetoceanProvider()

# Global instances (lazy loading fallback)
satellite_provider = get_satellite_provider()
ais_provider = get_ais_provider()
metocean_provider = get_metocean_provider()
