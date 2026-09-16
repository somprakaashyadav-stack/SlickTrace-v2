from pydantic import BaseModel, Field
from typing import List

class CandidatePriority(BaseModel):
    rank: int = Field(0, description="Investigation priority rank")
    mmsi: int
    vessel_name: str
    vessel_type: str
    
    # All scores normalized 0-100
    initial_score: int
    spatial_score: int
    temporal_score: int
    trajectory_score: int
    behavior_score: int
    ais_score: int
    capability_score: int
    
    positive_evidence: List[str] = Field(description="Evidence consistency aligning with spill")
    negative_evidence: List[str] = Field(description="Evidence inconsistencies")

class InitialScoreResponse(BaseModel):
    spill_id: str
    candidates: List[CandidatePriority]
