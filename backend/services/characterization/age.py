from typing import Dict, Any, Tuple

def estimate_age(elongation_ratio: float, fragmentation_index: float, wind_speed_knots: float = 10.0) -> Tuple[float, float, list[str]]:
    """
    ESTIMATED age calculation based on observable morphological indicators.
    DO NOT PRESENT AS GROUND TRUTH.
    
    Returns:
        estimated_age_hours: float
        confidence: float
        indicators_used: list[str]
    """
    indicators_used = []
    
    # Base age assumed from simple morphological breakdown
    # A perfectly fresh spill is compact (low elongation, low fragmentation)
    # Over time, wind and current stretch it (high elongation) and break it up (high fragmentation)
    
    age_hours = 0.0
    confidence = 0.8
    
    # Elongation contribution
    if elongation_ratio > 5.0:
        age_hours += 12.0
        indicators_used.append("High Elongation (>5.0) suggests significant drifting/spreading.")
    elif elongation_ratio > 2.0:
        age_hours += 4.0
        indicators_used.append("Moderate Elongation suggests recent spreading.")
    else:
        indicators_used.append("Low Elongation suggests recent discharge or continuous leak.")
        
    # Fragmentation contribution
    if fragmentation_index > 1.5:
        age_hours += 8.0
        indicators_used.append("High Fragmentation (>1.5) suggests weathering and wave-induced breakup.")
        confidence -= 0.1 # More fragmented = harder to estimate
    elif fragmentation_index > 1.2:
        age_hours += 3.0
        indicators_used.append("Moderate Fragmentation suggests early weathering.")
    else:
        indicators_used.append("Low Fragmentation (compact boundary) suggests fresh oil.")
        
    # Wind speed interaction (high wind = faster weathering)
    if wind_speed_knots > 15.0 and age_hours > 0:
        age_hours *= 0.8 # Weathered faster, so it might be younger than it looks
        indicators_used.append("High wind speed adjusted apparent weathering age downwards.")
        confidence -= 0.1
        
    # Ensure a minimum age if it's been detected
    age_hours = max(1.0, round(age_hours, 1))
    confidence = round(max(0.1, confidence), 2)
    
    return age_hours, confidence, indicators_used
