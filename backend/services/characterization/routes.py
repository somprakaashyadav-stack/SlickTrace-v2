from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from backend.services.characterization.schemas import SlickProfile
from backend.services.characterization.geometry import characterize_slick
from backend.services.characterization.age import estimate_age
from backend.services.detection.inference import inference_engine
from backend.demo_service import demo_service
import logging

router = APIRouter(prefix="/characterization", tags=["characterization"])
logger = logging.getLogger("slicktrace.characterization")

_PROFILE_CACHE: Dict[str, SlickProfile] = {}

@router.post("/{spill_id}", response_model=SlickProfile)
def run_characterization(spill_id: str):
    """
    Run the characterization pipeline on a detected oil spill polygon.
    """
    logger.info(f"Running characterization for spill {spill_id}")
    
    # Get detection result to access the polygon
    detection_result = inference_engine.get_cached_result(spill_id)
    if not detection_result or not detection_result.slick_polygon:
        raise HTTPException(status_code=404, detail=f"No valid segmentation polygon found for spill {spill_id}")
    
    polygon = detection_result.slick_polygon
    area_km2 = detection_result.slick_area_km2
    perimeter_km = detection_result.slick_perimeter_km
    
    # Calculate geometries
    geo_stats = characterize_slick(polygon, area_km2, perimeter_km)
    
    # Get metocean data for age estimation
    met = demo_service.get_demo_metocean()
    wind_knots = met.get("wind", {}).get("speed_knots", 10.0)
    
    # Estimate age
    age_hours, confidence, indicators = estimate_age(
        elongation_ratio=geo_stats["elongation_ratio"],
        fragmentation_index=geo_stats["fragmentation_index"],
        wind_speed_knots=wind_knots
    )
    
    profile = SlickProfile(
        spill_id=spill_id,
        centroid=geo_stats["centroid"],
        area_km2=area_km2,
        perimeter_km=perimeter_km,
        length_km=geo_stats["length_km"],
        width_km=geo_stats["width_km"],
        orientation_deg=geo_stats["orientation_deg"],
        elongation_ratio=geo_stats["elongation_ratio"],
        fragmentation_index=geo_stats["fragmentation_index"],
        estimated_age_hours=age_hours,
        age_confidence=confidence,
        bounding_box=geo_stats["bounding_box"],
        age_indicators_used=indicators
    )
    
    _PROFILE_CACHE[spill_id] = profile
    return profile

@router.get("/{spill_id}", response_model=SlickProfile)
def get_characterization(spill_id: str):
    """
    Get the cached characterization profile for a spill.
    """
    if spill_id in _PROFILE_CACHE:
        return _PROFILE_CACHE[spill_id]
        
    # If not in cache, try running it
    return run_characterization(spill_id)
