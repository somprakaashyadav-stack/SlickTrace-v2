"""
SlickTrace v2 — OpenDrift OpenOil Simulation & Uncertainty Configuration

Stores all physical simulation parameters for complete reproducibility:
- Oil physical and weathering characteristics
- Monte Carlo particle counts and dispersion parameters
- Windage drift factor ranges (2% - 4%)
- Turbulent diffusion coefficients
- Configurable duration horizons (e.g. 4h, 8h, 12h, 24h)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OilParameters:
    """Physical properties of the spilled substance."""
    oil_type: str = "GENERIC BUNKER C"
    api_gravity: float = 12.5
    viscosity_cst: float = 380.0
    pour_point_c: float = 15.0
    emulsification_max_water: float = 0.80

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HindcastSimulationConfig:
    """
    Complete configuration parameters for OpenOil backward Lagrangian hindcast.
    Guarantees full run reproducibility when combined with random_seed and forcing SHA-256.
    """
    durations_hours: List[int] = field(default_factory=lambda: [4, 8, 12, 24])
    n_particles: int = 1000
    horizontal_diffusivity_m2s: float = 10.0  # Turbulent horizontal diffusion
    wind_drift_factor_min: float = 0.02       # 2% windage
    wind_drift_factor_max: float = 0.04       # 4% windage
    current_drift_factor: float = 1.0         # 100% surface current coupling
    stokes_drift_factor: float = 1.0          # Wave Stokes drift coupling
    random_seed: Optional[int] = 42           # Fixed seed for Monte Carlo reproducibility
    time_step_minutes: int = -60              # Backward 1-hour time stepping
    oil_params: OilParameters = field(default_factory=OilParameters)

    def __post_init__(self):
        if not self.durations_hours:
            self.durations_hours = [4, 8, 12, 24]
        self.durations_hours = sorted(set(int(h) for h in self.durations_hours))
        if self.n_particles < 50:
            raise ValueError(f"n_particles must be at least 50 for Monte Carlo dispersion, got {self.n_particles}")

    @property
    def max_duration_hours(self) -> int:
        return max(self.durations_hours)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["oil_params"] = self.oil_params.to_dict()
        return d
