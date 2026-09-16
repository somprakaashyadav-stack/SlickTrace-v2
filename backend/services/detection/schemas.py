from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DetectionRunRequest(BaseModel):
    scene_id: Optional[str] = Field("S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI", description="Preprocessed scene ID to segment")
    model_architecture: str = Field("U-Net", description="Interchangeable PyTorch segmentation model architecture: 'U-Net' or 'DeepLabV3+'")
    confidence_threshold: float = Field(0.85, description="Segmentation probability cut-off threshold")

class LookalikeCheckDetail(BaseModel):
    check_name: str
    passed: bool
    risk_score: float
    reason: str

class DetectionResultResponse(BaseModel):
    spill_id: str
    scene_id: str
    model_name: str
    inference_mode: str
    detection_confidence: float
    segmentation_status: str
    slick_area_km2: float
    slick_perimeter_km: float
    slick_polygon: List[List[float]]
    lookalike_checks: List[LookalikeCheckDetail]
    candidate_mask_count: int
    stats: Dict[str, Any]
