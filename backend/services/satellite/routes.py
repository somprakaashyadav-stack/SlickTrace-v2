from fastapi import APIRouter, HTTPException
from backend.services.satellite.schemas import (
    SatelliteProcessRequest,
    SatelliteProcessResponse,
    SatelliteStatusResponse
)
from backend.services.providers.factory import satellite_provider
from backend.services.providers.satellite import DemoSatelliteProvider
from backend.services.satellite.preprocessing import preprocessing_pipeline

router = APIRouter(prefix="/satellite", tags=["Satellite Preprocessing Module"])

@router.get("/status", response_model=SatelliteStatusResponse)
def get_satellite_status():
    """Returns satellite module operational status and ready granules."""
    try:
        meta = satellite_provider.get_granule_metadata("S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI")
        mode = "REAL" if not isinstance(satellite_provider, DemoSatelliteProvider) else "DEMO"
    except Exception:
        # Graceful fallback for status
        demo = DemoSatelliteProvider()
        meta = demo.get_granule_metadata("S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI")
        mode = "DEMO (Fallback)"
        
    return {
        "service_status": "ONLINE",
        "copernicus_api_ready": mode == "REAL", 
        "demo_mode": "DEMO" in mode,
        "available_demo_granules": [meta]
    }

@router.post("/process", response_model=SatelliteProcessResponse)
def process_satellite_scene(request: SatelliteProcessRequest = SatelliteProcessRequest()):
    """
    Executes satellite data ingestion and 5-stage preprocessing pipeline:
    Data Ingestion -> Radiometric Calibration [DEMO/PLACEHOLDER] -> Lee Speckle Filter -> Terrain Correction [DEMO/PLACEHOLDER] -> Land Masking -> Normalization.
    """
    try:
        raw_scene = satellite_provider.fetch_raw_scene_data(request.scene_id)
    except Exception:
        # Graceful Fallback
        demo = DemoSatelliteProvider()
        raw_scene = demo.fetch_raw_scene_data(request.scene_id)
        
    try:
        result = preprocessing_pipeline.execute_pipeline(raw_scene)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Satellite preprocessing error: {str(e)}")
