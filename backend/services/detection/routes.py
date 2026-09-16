from fastapi import APIRouter, HTTPException
from backend.services.detection.schemas import DetectionRunRequest, DetectionResultResponse
from backend.services.detection.inference import inference_engine

router = APIRouter(prefix="/detection", tags=["Oil Spill Detection Module"])

@router.post("/run", response_model=DetectionResultResponse)
def run_oil_spill_detection(request: DetectionRunRequest = DetectionRunRequest()):
    """
    Triggers AI segmentation pipeline (interchangeable U-Net / DeepLabV3+) and Look-Alike Rejection filters.
    Honest reporting: returns 'DEMO / SYNTHETIC' if no weights in models/, or 'MODEL MODE' when trained weights are loaded.
    """
    try:
        result = inference_engine.run_detection(
            scene_id=request.scene_id,
            architecture=request.model_architecture,
            confidence_threshold=request.confidence_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection inference error: {str(e)}")

@router.get("/result/{spill_id}", response_model=DetectionResultResponse)
def get_detection_result(spill_id: str):
    """Retrieves segmentation result and look-alike rejection scorecard for a given spill ID."""
    result = inference_engine.get_cached_result(spill_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Spill detection result for ID '{spill_id}' not found.")
    return result
