from backend.services.ais.schemas import CandidateVessel
from backend.services.anomaly.schemas import AnomalyResult
from backend.services.scoring.schemas import CandidatePriority
from backend.services.scoring.config import SCORING_WEIGHTS

def calculate_capability_score(vessel_type: str) -> float:
    """
    Returns a normalized score (0.0 to 1.0) indicating how capable the 
    vessel type is of generating a significant oil slick.
    """
    vt = vessel_type.lower()
    if "tanker" in vt:
        return 1.0
    elif "cargo" in vt or "bulk" in vt or "container" in vt:
        return 0.7
    elif "supply" in vt or "support" in vt:
        return 0.5
    elif "fishing" in vt or "trawler" in vt:
        return 0.2
    else:
        return 0.1

def generate_evidence(candidate: CandidateVessel, anomaly: AnomalyResult, cap_score: float) -> tuple[list[str], list[str]]:
    positive_evidence = []
    negative_evidence = []
    
    # 1. Spatial Evidence
    if candidate.scores.spatial_score > 0.8:
        positive_evidence.append("Spatial alignment: Vessel track intersects the core uncertainty origin cone.")
    elif candidate.scores.spatial_score < 0.2:
        negative_evidence.append("Spatial inconsistency: Vessel transit is geographically distant from origin cone.")
        
    # 2. Temporal Evidence
    if candidate.scores.temporal_score > 0.8:
        positive_evidence.append("Temporal alignment: Vessel presence coincides precisely with estimated release time (T0).")
    elif candidate.scores.temporal_score < 0.2:
        negative_evidence.append("Temporal inconsistency: Vessel traversed the area significantly before or after T0.")
        
    # 3. AIS Gap Evidence
    if anomaly.gap_details.classification == "potentially_anomalous":
        positive_evidence.append(f"Suspicious AIS Gap: {anomaly.gap_details.reason}")
    elif candidate.reconstructed_points == 0:
        negative_evidence.append("Continuous telemetry: No AIS transponder gaps detected.")
        
    # 4. Behavioral Evidence
    if anomaly.speed_details.detected:
        positive_evidence.append(f"Anomalous Behavior: {anomaly.speed_details.reason}")
    if anomaly.course_details.detected:
        positive_evidence.append(f"Anomalous Behavior: {anomaly.course_details.reason}")
    if anomaly.stop_details.detected:
        positive_evidence.append(f"Anomalous Behavior: {anomaly.stop_details.reason}")
        
    # 5. ML Trajectory Evidence
    if anomaly.trajectory_anomaly_score > 0.7:
        positive_evidence.append("ML Isolation Forest flags trajectory baseline as highly anomalous.")
        
    # 6. Capability Evidence
    if cap_score >= 0.7:
        positive_evidence.append(f"Vessel profile ({candidate.vessel_type}) is highly capable of significant discharges.")
    elif cap_score <= 0.3:
        negative_evidence.append(f"Vessel profile ({candidate.vessel_type}) has low holding capacity for this spill volume.")
        
    return positive_evidence, negative_evidence

def compute_initial_score(candidate: CandidateVessel, anomaly: AnomalyResult) -> CandidatePriority:
    cap_score_raw = calculate_capability_score(candidate.vessel_type)
    
    # Base scores (0-1) from CandidateVessel
    s_space = candidate.scores.spatial_score
    s_time = candidate.scores.temporal_score
    s_traj = candidate.scores.trajectory_score
    
    # Behavior & AIS scores from AnomalyResult (Severity is 0-1)
    s_behavior = max([
        anomaly.speed_details.severity, 
        anomaly.course_details.severity, 
        anomaly.stop_details.severity
    ])
    s_ais = max(anomaly.ais_gap_score, anomaly.trajectory_anomaly_score)
    s_cap = cap_score_raw
    
    # Apply weights
    raw_score = (
        (s_space * SCORING_WEIGHTS["w_space"]) +
        (s_time * SCORING_WEIGHTS["w_time"]) +
        (s_traj * SCORING_WEIGHTS["w_trajectory"]) +
        (s_behavior * SCORING_WEIGHTS["w_behavior"]) +
        (s_ais * SCORING_WEIGHTS["w_ais"]) +
        (s_cap * SCORING_WEIGHTS["w_capability"])
    )
    
    # Normalize 0-100
    initial_score = int(min(100, max(0, round(raw_score * 100))))
    
    positive_evidence, negative_evidence = generate_evidence(candidate, anomaly, cap_score_raw)
    
    return CandidatePriority(
        rank=0, # Will be set by router after sorting
        mmsi=candidate.mmsi,
        vessel_name=candidate.vessel_name,
        vessel_type=candidate.vessel_type,
        initial_score=initial_score,
        spatial_score=int(round(s_space * 100)),
        temporal_score=int(round(s_time * 100)),
        trajectory_score=int(round(s_traj * 100)),
        behavior_score=int(round(s_behavior * 100)),
        ais_score=int(round(s_ais * 100)),
        capability_score=int(round(s_cap * 100)),
        positive_evidence=positive_evidence,
        negative_evidence=negative_evidence
    )
