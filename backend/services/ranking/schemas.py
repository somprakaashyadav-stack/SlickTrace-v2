from pydantic import BaseModel, Field
from typing import List, Optional

class FinalCandidateRanking(BaseModel):
    rank: int
    vessel_name: str
    mmsi: int
    vessel_type: str
    initial_score: int
    physics_score: int
    final_score: int
    rank_change: int
    evidence_for: List[str]
    evidence_against: List[str]
    ais_reliability: str
    investigation_priority: str
    rank_change_explanation: str

class FinalRankingResponse(BaseModel):
    spill_id: str
    alpha_weight: float
    beta_weight: float
    rankings: List[FinalCandidateRanking]
