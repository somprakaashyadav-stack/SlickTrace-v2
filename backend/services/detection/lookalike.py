"""
Look-Alike Rejection Engine for SlickTrace v2
Evaluates candidate dark spot masks against environmental and spatial false positive factors:
- Low-wind regions (wind speed < 3.0 m/s causing calm water specular reflection)
- Ship wake geometry (narrow linear trails following vessels)
- Algae / biological bloom signatures
- Aspect ratio and edge damping steepness
"""
import math
from typing import Dict, Any, List, Tuple
from backend.services.detection.schemas import LookalikeCheckDetail

class LookalikeRejectionEngine:
    def __init__(self):
        pass

    def evaluate_candidate(
        self,
        wind_speed_knots: float = 14.2,
        sea_temp_c: float = 28.5,
        closest_vessel_dist_km: float = 0.45,
        area_km2: float = 14.85,
        perimeter_km: float = 18.40
    ) -> Tuple[bool, List[LookalikeCheckDetail], float]:
        """
        Executes look-alike rejection filters.
        Returns: (is_valid_slick, list_of_check_details, overall_confidence_adjustment)
        """
        checks: List[LookalikeCheckDetail] = []
        
        # 1. Low-Wind Calm Zone Check (Wind < 6 knots / ~3 m/s causes specular dark ocean look-alikes)
        wind_ms = wind_speed_knots * 0.514444
        if wind_ms < 3.0:
            checks.append(LookalikeCheckDetail(
                check_name="Low-Wind Calm Region Filter",
                passed=False,
                risk_score=85.0,
                reason=f"Wind speed ({wind_ms:.1f} m/s) is below 3.0 m/s threshold; high risk of wind-calm specular dark spot."
            ))
        else:
            checks.append(LookalikeCheckDetail(
                check_name="Low-Wind Calm Region Filter",
                passed=True,
                risk_score=10.0,
                reason=f"Wind speed ({wind_ms:.1f} m/s) is sufficient (> 3.0 m/s) to generate surface capillary waves."
            ))

        # 2. Ship Wake Geometry Filter
        if closest_vessel_dist_km < 0.1:
            checks.append(LookalikeCheckDetail(
                check_name="Ship Wake Geometry Filter",
                passed=False,
                risk_score=75.0,
                reason="Feature overlaps directly with active vessel wake track."
            ))
        else:
            checks.append(LookalikeCheckDetail(
                check_name="Ship Wake Geometry Filter",
                passed=True,
                risk_score=15.0,
                reason="Feature is spatially distinct from vessel hydrodynamic wake axis."
            ))

        # 3. Algae / Biological Bloom Filter (High SST > 31°C combined with low wind promotes algal films)
        if sea_temp_c > 31.0 and wind_ms < 4.0:
            checks.append(LookalikeCheckDetail(
                check_name="Algae / Biological Bloom Filter",
                passed=False,
                risk_score=65.0,
                reason="Sea surface temperature (> 31°C) and low turbulence suggest potential macroalgae bloom."
            ))
        else:
            checks.append(LookalikeCheckDetail(
                check_name="Algae / Biological Bloom Filter",
                passed=True,
                risk_score=12.0,
                reason="Environmental parameters favor mineral oil slick over biological surfactant."
            ))

        # 4. Aspect Ratio & Edge Damping Filter (Compactness = 4 * pi * Area / Perimeter^2)
        compactness = (4 * math.pi * area_km2) / (perimeter_km ** 2 + 1e-6)
        if compactness > 0.85:
            checks.append(LookalikeCheckDetail(
                check_name="Shape Compactness & Edge Damping Filter",
                passed=False,
                risk_score=60.0,
                reason=f"Compactness ({compactness:.2f}) is overly circular, typical of cloud shadow or rain cell."
            ))
        else:
            checks.append(LookalikeCheckDetail(
                check_name="Shape Compactness & Edge Damping Filter",
                passed=True,
                risk_score=10.0,
                reason=f"Elongated aspect ratio (Compactness: {compactness:.2f}) consistent with oil slick dispersion."
            ))

        # Calculate final verdict
        all_passed = all(c.passed for c in checks)
        avg_risk = sum(c.risk_score for c in checks) / len(checks)
        confidence = round(max(0.40, 1.0 - (avg_risk / 100.0)), 2)

        return all_passed, checks, confidence

lookalike_engine = LookalikeRejectionEngine()
