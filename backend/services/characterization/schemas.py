from pydantic import BaseModel, Field
from typing import List

class SlickProfile(BaseModel):
    spill_id: str
    centroid: List[float] = Field(description="[longitude, latitude]")
    area_km2: float
    perimeter_km: float
    length_km: float
    width_km: float
    orientation_deg: float
    elongation_ratio: float
    fragmentation_index: float
    estimated_age_hours: float
    age_confidence: float
    bounding_box: List[List[float]] = Field(description="[[min_lon, min_lat], [max_lon, max_lat]]")
    age_indicators_used: List[str] = Field(default_factory=list)
