from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from backend.services.drift.particles import DemoLagrangianModel

logger = logging.getLogger(__name__)

class PhysicsEngine(ABC):
    @abstractmethod
    def run_simulation(
        self, start_lat: float, start_lon: float, start_time: datetime,
        hours: int, reverse: bool = False, num_particles: int = 100,
        wind_knots: float = 10.0, wind_dir: float = 210.0,
        current_knots: float = 0.5, current_dir: float = 90.0
    ) -> List[List[Dict[str, Any]]]:
        """
        Executes a drift simulation.
        Returns a list of particle trajectories. Each trajectory is a list of points:
        [ {"lat": float, "lon": float, "timestamp": str}, ... ]
        """
        pass

class DemoPhysicsEngine(PhysicsEngine):
    def run_simulation(
        self, start_lat: float, start_lon: float, start_time: datetime,
        hours: int, reverse: bool = False, num_particles: int = 100,
        wind_knots: float = 10.0, wind_dir: float = 210.0,
        current_knots: float = 0.5, current_dir: float = 90.0
    ) -> List[List[Dict[str, Any]]]:
        model = DemoLagrangianModel(
            wind_speed_knots=wind_knots,
            wind_dir_deg=wind_dir,
            current_speed_knots=current_knots,
            current_dir_deg=current_dir
        )
        return model.propagate(
            start_lat=start_lat,
            start_lon=start_lon,
            start_time=start_time,
            hours=hours,
            reverse=reverse,
            num_particles=num_particles
        )

class OpenDriftPhysicsEngine(PhysicsEngine):
    def run_simulation(
        self, start_lat: float, start_lon: float, start_time: datetime,
        hours: int, reverse: bool = False, num_particles: int = 100,
        wind_knots: float = 10.0, wind_dir: float = 210.0,
        current_knots: float = 0.5, current_dir: float = 90.0
    ) -> List[List[Dict[str, Any]]]:
        try:
            from opendrift.models.openoil import OpenOil
            import xarray as xr
        except ImportError:
            logger.error("OpenDrift library is not installed.")
            raise RuntimeError("Configuration Error: OpenDrift library is not installed. Please set DRIFT_ENGINE=demo or install OpenDrift.")
            
        logger.info("Initializing OpenOil (OpenDrift) model...")
        o = OpenOil()
        
        # Here we would normally add readers for wind and current (e.g., from metocean_provider netcdf)
        # o.add_readers_from_list(['path_to_wind.nc', 'path_to_current.nc'])
        
        # Seed elements
        o.seed_elements(lon=start_lon, lat=start_lat, radius=1000, number=num_particles, time=start_time)
        
        # Calculate duration and time step
        duration = timedelta(hours=hours)
        time_step = timedelta(hours=1)
        
        if reverse:
            time_step = -time_step
            
        # Run simulation
        o.run(duration=duration, time_step=time_step, time_step_output=time_step)
        
        # Extract trajectories from history to match our schema
        history = o.history
        lons = history['lon'].values
        lats = history['lat'].values
        times = history['time'].values
        
        trajectories = []
        for i in range(num_particles):
            traj = []
            for t_idx, t in enumerate(times):
                lon = lons[i, t_idx]
                lat = lats[i, t_idx]
                if str(lon) != 'nan' and str(lat) != 'nan':
                    traj.append({
                        "lat": float(lat),
                        "lon": float(lon),
                        "timestamp": str(t)
                    })
            if traj:
                trajectories.append(traj)
                
        return trajectories

def get_physics_engine() -> PhysicsEngine:
    from backend.config import settings
    if settings.DRIFT_ENGINE.lower() == "opendrift":
        return OpenDriftPhysicsEngine()
    return DemoPhysicsEngine()
