from fastapi import APIRouter, HTTPException
from backend.services.reporting.schemas import ReportGenerationResponse
from backend.services.reporting.generator import ReportGenerator

router = APIRouter(prefix="/report", tags=["Reporting Module"])
generator = ReportGenerator()

@router.post("/generate/{spill_id}", response_model=ReportGenerationResponse)
def generate_investigation_report(spill_id: str):
    """
    Generates a PDF SlickTrace v2 Investigation Support Report for the given spill_id.
    """
    try:
        report_path = generator.generate_pdf(spill_id)
        return ReportGenerationResponse(
            spill_id=spill_id,
            report_path=report_path,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
