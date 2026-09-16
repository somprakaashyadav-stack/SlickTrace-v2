import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from backend.services.detection.routes import get_detection_result
from backend.services.characterization.routes import get_characterization
from backend.services.drift.origin_routes import get_origin_cone
from backend.services.ranking.routes import get_final_ranking
from backend.demo_service import demo_service

class ReportGenerator:
    def __init__(self):
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles["Title"]
        self.h1_style = self.styles["Heading1"]
        self.h2_style = self.styles["Heading2"]
        self.normal_style = self.styles["Normal"]

    def _safe_call(self, func, *args):
        try:
            return func(*args)
        except Exception:
            return None

    def generate_pdf(self, spill_id: str) -> str:
        report_path = os.path.join(self.output_dir, f"{spill_id}_investigation_report.pdf")
        doc = SimpleDocTemplate(report_path, pagesize=letter)
        story = []

        # Title
        story.append(Paragraph("SlickTrace v2 Investigation Support Report", self.title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()}Z", self.normal_style))
        story.append(Spacer(1, 24))

        # Fetch Data
        spill = demo_service.get_demo_spill()
        detection = self._safe_call(get_detection_result, spill_id)
        char = self._safe_call(get_characterization, spill_id)
        origin = self._safe_call(get_origin_cone, spill_id)
        ranking = self._safe_call(get_final_ranking, spill_id)

        # 1-7. Case Summary & Satellite / Slick
        story.append(Paragraph("1. Case Summary & Satellite Observation", self.h1_style))
        story.append(Paragraph(f"Spill ID: {spill_id}", self.normal_style))
        story.append(Paragraph(f"Observation Time: {spill.get('timestamp', 'N/A')}", self.normal_style))
        if detection:
            story.append(Paragraph(f"Detection Confidence: {detection.detection_confidence*100:.1f}%", self.normal_style))
            story.append(Paragraph(f"Model Used: {detection.model_name}", self.normal_style))
        if char:
            story.append(Paragraph(f"Area: {char.area_km2:.2f} sq km", self.normal_style))
            story.append(Paragraph(f"Estimated Age: {char.estimated_age_hours} hours", self.normal_style))
        story.append(Spacer(1, 12))

        # 8-10. Drift & Origin
        story.append(Paragraph("2. Drift Analysis & Origin Estimation", self.h1_style))
        if origin and origin.probable_origin:
            po = origin.probable_origin
            story.append(Paragraph(f"Estimated Origin Centroid: {po.Y0:.4f}, {po.X0:.4f}", self.normal_style))
            story.append(Paragraph(f"Release Time Window: {origin.time_window_start} to {origin.time_window_end}", self.normal_style))
            story.append(Paragraph(f"Uncertainty Radius: {po.uncertainty_radius_km} km", self.normal_style))
        else:
            story.append(Paragraph("Drift data not available.", self.normal_style))
        story.append(Spacer(1, 12))

        # 11-18. Candidate Ranking & Evidence
        story.append(Paragraph("3. Final Candidate Ranking & Evidence", self.h1_style))
        if ranking and ranking.rankings:
            data = [["Rank", "MMSI", "Vessel Name", "Final Score", "Phys. Score"]]
            for r in ranking.rankings:
                data.append([
                    str(r.rank),
                    str(r.mmsi),
                    r.vessel_name,
                    f"{r.final_score:.1f}",
                    f"{r.physics_score:.1f}" if r.physics_score is not None else "N/A"
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Evidence Breakdown
            story.append(Paragraph("Detailed Candidate Evidence:", self.h2_style))
            for r in ranking.rankings:
                story.append(Paragraph(f"Vessel: {r.vessel_name} (MMSI: {r.mmsi})", self.styles["Heading3"]))
                story.append(Paragraph(f"Rank Change: {'+' if r.rank_change > 0 else ''}{r.rank_change}", self.normal_style))
                story.append(Paragraph(f"Rank Rationale: {r.rank_change_explanation}", self.normal_style))
                
                if r.evidence_for:
                    story.append(Paragraph("Evidence Consistency (Positive):", self.normal_style))
                    for ev in r.evidence_for:
                        story.append(Paragraph(f"- {ev}", self.normal_style))
                
                if r.evidence_against:
                    story.append(Paragraph("Evidence Inconsistency (Negative):", self.normal_style))
                    for ev in r.evidence_against:
                        story.append(Paragraph(f"- {ev}", self.normal_style))
                        
                story.append(Spacer(1, 6))

        else:
            story.append(Paragraph("Ranking data not available.", self.normal_style))
        
        story.append(Spacer(1, 12))

        # 19-20. Limitations & Human Investigator Decision
        story.append(Paragraph("4. Limitations", self.h1_style))
        story.append(Paragraph("This report is strictly for investigation support and prioritization. It DOES NOT constitute proof of responsibility or guilt. Physics verification denotes physical consistency with the observed slick, not absolute causality. Some data points may be derived from synthetic or demo sources if live integration was unavailable.", self.normal_style))
        story.append(Spacer(1, 24))

        story.append(Paragraph("5. Human Investigator Decision Section", self.h1_style))
        story.append(Paragraph("Investigator Name: ___________________________", self.normal_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Signature: ___________________________________", self.normal_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Date: ________________________________________", self.normal_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Decision / Next Steps:", self.normal_style))
        story.append(Spacer(1, 40))
        story.append(Paragraph("________________________________________________________________________________", self.normal_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("________________________________________________________________________________", self.normal_style))

        doc.build(story)
        return report_path
