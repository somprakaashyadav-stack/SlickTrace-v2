from pydantic import BaseModel, Field
from typing import Optional, List

class AnomalyExplainability(BaseModel):
    detected: bool
    classification: str = Field(description="e.g. 'potentially_anomalous', 'normal_dropout', 'normal', 'suspicious'")
    reason: str
    duration_minutes: Optional[float] = None
    severity: float = Field(0.0, description="Severity score 0 to 1")

class AnomalyResult(BaseModel):
    mmsi: int
    speed_anomaly_score: float
    course_deviation_score: float
    ais_gap_score: float
    trajectory_anomaly_score: float
    
    speed_details: AnomalyExplainability
    course_details: AnomalyExplainability
    gap_details: AnomalyExplainability
    stop_details: AnomalyExplainability
    
    overall_anomaly_flag: bool
