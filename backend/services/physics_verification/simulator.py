from typing import List, Tuple
from backend.services.physics_verification.schemas import PhysicsScenario
from backend.services.drift.physics_engine import get_physics_engine
from backend.services.ais.cleaning import parse_time
from datetime import datetime

class PhysicsSimulator:
    def simulate_forward(self, scenario: PhysicsScenario, num_particles: int = 100) -> List[Tuple[float, float]]:
        engine = get_physics_engine()
        
        base_wind_speed = 10.0
        base_wind_dir = 210.0
        base_current_speed = 0.5
        base_current_dir = 90.0
        
        wind_knots = max(0.0, base_wind_speed + scenario.wind_variance * 5.0)
        wind_dir = (base_wind_dir + scenario.wind_variance * 10.0) % 360
        current_knots = max(0.0, base_current_speed + scenario.current_variance)
        current_dir = (base_current_dir + scenario.current_variance * 10.0) % 360
        
        start_time = parse_time(scenario.release_time)
        hours = max(1, int(scenario.duration_hours))
        
        trajectories = engine.run_simulation(
            start_lat=scenario.release_lat,
            start_lon=scenario.release_lon,
            start_time=start_time,
            hours=hours,
            reverse=False,
            num_particles=num_particles,
            wind_knots=wind_knots,
            wind_dir=wind_dir,
            current_knots=current_knots,
            current_dir=current_dir
        )
        
        final_particles = []
        for traj in trajectories:
            last_pt = traj[-1]
            final_particles.append((last_pt["lon"], last_pt["lat"]))
            
        return final_particles
