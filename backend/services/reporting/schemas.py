from pydantic import BaseModel

class ReportGenerationResponse(BaseModel):
    spill_id: str
    report_path: str
    status: str
