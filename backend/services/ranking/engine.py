from typing import List, Dict, Any
from backend.services.ranking.schemas import FinalCandidateRanking
from backend.services.ranking.config import ranking_config

def generate_explanation(vessel_name: str, rank_change: int, initial_rank: int, final_rank: int, physics_score: int, initial_score: int) -> str:
    if rank_change == 0:
        return f"Maintained Rank {final_rank} as physical consistency ({physics_score}/100) aligned with behavioral score ({initial_score}/100)."
    
    direction = "Moved up" if rank_change > 0 else "Moved down"
    
    reason = "high physical consistency with the observed slick" if physics_score >= 70 else "low physical consistency with the observed slick"
    
    if rank_change < 0 and physics_score < 50:
        reason = "physical simulation showed poor spatial consistency with the observed slick."
    elif rank_change > 0 and physics_score >= 70:
        reason = "forward simulation demonstrated strong convergence with the observed slick."
        
    return f"{direction} from Rank {initial_rank} to Rank {final_rank} because {reason}"

def calculate_priority(final_score: int) -> str:
    if final_score >= 75:
        return "HIGH PRIORITY"
    elif final_score >= 50:
        return "MEDIUM PRIORITY"
    else:
        return "LOW PRIORITY"

def compute_final_rankings(initial_candidates: List[Any], physics_results: List[Any]) -> List[FinalCandidateRanking]:
    # initial_candidates: List[CandidatePriority] from scoring engine
    # physics_results: List[PhysicsVerificationResult] from physics engine
    
    # Map by MMSI
    initial_map = {c.mmsi: {"candidate": c, "initial_rank": c.rank} for c in initial_candidates}
    physics_map = {r.mmsi: r for r in physics_results}
    
    combined = []
    
    for mmsi, data in initial_map.items():
        candidate = data["candidate"]
        init_rank = data["initial_rank"]
        
        phys_result = physics_map.get(mmsi)
        
        # If no physics result (not in top N), physics score is 0
        phys_score = phys_result.physics_consistency_score if phys_result else 0
        
        # Calculate final score
        final_score = (ranking_config.ALPHA_WEIGHT * candidate.initial_score) + (ranking_config.BETA_WEIGHT * phys_score)
        
        # Build evidence
        evidence_for = list(candidate.positive_evidence)
        evidence_against = list(candidate.negative_evidence)
        
        if phys_result:
            if phys_score >= 70:
                evidence_for.append("High physical consistency observed in forward simulation.")
            else:
                evidence_against.append("Low physical consistency in forward simulation.")
        else:
            evidence_against.append("Physics verification not run due to low initial priority.")
            
        combined.append({
            "mmsi": mmsi,
            "vessel_name": candidate.vessel_name,
            "vessel_type": candidate.vessel_type,
            "initial_score": candidate.initial_score,
            "physics_score": phys_score,
            "final_score": int(round(final_score)),
            "initial_rank": init_rank,
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "ais_reliability": "HIGH" if candidate.ais_score > 70 else "MODERATE"
        })
        
    # Sort by final score descending
    combined.sort(key=lambda x: x["final_score"], reverse=True)
    
    final_rankings = []
    for idx, item in enumerate(combined):
        final_rank = idx + 1
        rank_change = item["initial_rank"] - final_rank # Positive means moved up (e.g. from 3 to 1 -> +2)
        
        explanation = generate_explanation(
            item["vessel_name"], 
            rank_change, 
            item["initial_rank"], 
            final_rank, 
            item["physics_score"], 
            item["initial_score"]
        )
        
        final_rankings.append(
            FinalCandidateRanking(
                rank=final_rank,
                vessel_name=item["vessel_name"],
                mmsi=item["mmsi"],
                vessel_type=item["vessel_type"],
                initial_score=item["initial_score"],
                physics_score=item["physics_score"],
                final_score=item["final_score"],
                rank_change=rank_change,
                evidence_for=item["evidence_for"],
                evidence_against=item["evidence_against"],
                ais_reliability=item["ais_reliability"],
                investigation_priority=calculate_priority(item["final_score"]),
                rank_change_explanation=explanation
            )
        )
        
    return final_rankings
