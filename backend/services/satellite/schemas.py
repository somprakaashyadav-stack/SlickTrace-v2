from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SatelliteProcessRequest(BaseModel):
    scene_id: Optional[str] = Field("S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI", description="Granule scene ID to preprocess")
    satellite: Optional[str] = Field("Sentinel-1B", description="Satellite sensor source (Sentinel-1B or Sentinel-2A)")
    filter_type: Optional[str] = Field("Lee (5x5)", description="Speckle reduction filter type")

class PreprocessingStepDetail(BaseModel):
    step_name: str
    status: str
    method: str
    is_placeholder: bool
    description: str

class SatelliteProcessResponse(BaseModel):
    scene_id: str
    satellite: str
    sensor: str
    acquisition_time: str
    polarization: str
    processing_status: str
    image_dimensions: List[int]
    preprocessing_steps: List[PreprocessingStepDetail]
    output_path_reference: str
    stats: Dict[str, Any]

class SatelliteStatusResponse(BaseModel):
    service_status: str
    copernicus_api_ready: bool
    demo_mode: bool
    available_demo_granules: List[Dict[str, Any]]
