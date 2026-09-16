import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_initial_scoring():
    res = client.post("/api/scoring/initial/test-spill")
    assert res.status_code == 200
    data = res.json()
    
    assert data["spill_id"] == "test-spill"
    assert len(data["candidates"]) > 0
    
    top_candidate = data["candidates"][0]
    
    print("\n--- TOP CANDIDATE ---")
    print(f"Rank: {top_candidate['rank']}")
    print(f"Vessel: {top_candidate['vessel_name']} ({top_candidate['vessel_type']})")
    print(f"Initial Priority Score: {top_candidate['initial_score']}")
    print("Breakdown:")
    print(f"  Spatial: {top_candidate['spatial_score']}")
    print(f"  Temporal: {top_candidate['temporal_score']}")
    print(f"  Trajectory: {top_candidate['trajectory_score']}")
    print(f"  Behavior: {top_candidate['behavior_score']}")
    print(f"  AIS Anomaly: {top_candidate['ais_score']}")
    print(f"  Capability: {top_candidate['capability_score']}")
    print("Positive Evidence:")
    for ev in top_candidate["positive_evidence"]:
        print(f"  + {ev}")
    print("Negative Evidence:")
    for ev in top_candidate["negative_evidence"]:
        print(f"  - {ev}")

    # Ensure forbidden terms aren't in evidence
    forbidden = ["guilty", "confirmed culprit", "100% responsible"]
    for ev in top_candidate["positive_evidence"] + top_candidate["negative_evidence"]:
        for term in forbidden:
            assert term not in ev.lower()
