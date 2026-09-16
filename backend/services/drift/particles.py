import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

class DemoLagrangianModel:
    """
    Simplified deterministic Lagrangian particle simulation for DEMO MODE.
    Uses wind (3% leeway) and surface current (100%) to advect particles.
    """
    def __init__(self, wind_speed_knots: float, wind_dir_deg: float, current_speed_knots: float, current_dir_deg: float):
        self.wind_speed_knots = wind_speed_knots
        self.wind_dir_deg = wind_dir_deg
        self.current_speed_knots = current_speed_knots
        self.current_dir_deg = current_dir_deg
        
        # Wind leeway factor (oil typically drifts at ~3% of wind speed)
        self.wind_factor = 0.03
        
        self.dt_seconds = 3600  # 1 hour steps
        
    def _calculate_velocity_vector(self, reverse: bool = False) -> Tuple[float, float]:
        """Returns advection vector (u, v) in meters per second."""
        # Convert knots to m/s
        knt_to_ms = 0.514444
        w_ms = self.wind_speed_knots * knt_to_ms * self.wind_factor
        c_ms = self.current_speed_knots * knt_to_ms
        
        # Convert meteorological angles (direction FROM) to mathematical angles
        # Or standard oceanographic (direction TO). Assuming direction TO for simplicity.
        # Wind 210 deg means blowing TO 210 (South-West)
        w_rad = math.radians(self.wind_dir_deg)
        c_rad = math.radians(self.current_dir_deg)
        
        # Calculate u (East), v (North) components
        u_w = w_ms * math.sin(w_rad)
        v_w = w_ms * math.cos(w_rad)
        
        u_c = c_ms * math.sin(c_rad)
        v_c = c_ms * math.cos(c_rad)
        
        u_total = u_w + u_c
        v_total = v_w + v_c
        
        if reverse:
            u_total = -u_total
            v_total = -v_total
            
        return u_total, v_total
        
    def _advect(self, lat: float, lon: float, u: float, v: float) -> Tuple[float, float]:
        """Advects a single point by (u, v) m/s for dt_seconds."""
        dy = v * self.dt_seconds
        dx = u * self.dt_seconds
        
        # Convert to degrees
        dlat = dy / 111320.0
        dlon = dx / (111320.0 * math.cos(math.radians(lat)))
        
        # Add random diffusion/walk
        dlat += np.random.normal(0, 0.0005)
        dlon += np.random.normal(0, 0.0005)
        
        return lat + dlat, lon + dlon

    def propagate(self, start_lat: float, start_lon: float, start_time: datetime, hours: int, reverse: bool = False, num_particles: int = 1) -> List[List[Dict[str, Any]]]:
        """
        Propagates particles backward or forward in time.
        """
        u, v = self._calculate_velocity_vector(reverse=reverse)
        
        trajectories = []
        for _ in range(num_particles):
            traj = []
            curr_lat = start_lat + np.random.normal(0, 0.002) # Initial spread
            curr_lon = start_lon + np.random.normal(0, 0.002)
            curr_time = start_time
            
            traj.append({
                "step": 0,
                "time": curr_time.isoformat(),
                "lat": curr_lat,
                "lon": curr_lon
            })
            
            for step in range(1, hours + 1):
                curr_lat, curr_lon = self._advect(curr_lat, curr_lon, u, v)
                if reverse:
                    curr_time -= timedelta(seconds=self.dt_seconds)
                else:
                    curr_time += timedelta(seconds=self.dt_seconds)
                    
                traj.append({
                    "step": step,
                    "time": curr_time.isoformat(),
                    "lat": round(curr_lat, 5),
                    "lon": round(curr_lon, 5)
                })
            trajectories.append(traj)
            
        return trajectories
