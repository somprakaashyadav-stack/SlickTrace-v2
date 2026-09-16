from fastapi import APIRouter
from backend.demo_service import demo_service
from backend.schemas import EvidenceReportResponse

router = APIRouter(prefix="/reports", tags=["Evidence Reports"])

@router.get("/dossier", response_model=EvidenceReportResponse)
def get_evidence_dossier():
    return demo_service.get_evidence_report()

@router.get("/{incident_id}/export")
def export_dossier(incident_id: str, format: str = "json"):
    data = demo_service.get_evidence_report()
    return {
        "status": "success",
        "incident_id": incident_id,
        "format": format,
        "payload": data
    }
